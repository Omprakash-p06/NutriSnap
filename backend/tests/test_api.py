"""Integration tests for the NutriSnap FastAPI."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nutrisnap.api.main import app, get_store
from nutrisnap.api.store import ResultStore
from nutrisnap.api.worker import JobWorker


@pytest.fixture
async def mock_store(tmp_path):
    # Use a temp DB for tests
    db_path = tmp_path / "test_nutrisnap.db"
    store = ResultStore(db_path=db_path)
    await store.initialize()
    return store


@pytest.fixture
def client(mock_store):
    # Register a worker for this store
    worker = JobWorker(mock_store)
    # Override dependencies
    from nutrisnap.api.main import get_worker

    app.dependency_overrides[get_store] = lambda: mock_store
    app.dependency_overrides[get_worker] = lambda: worker
    # Note: we use actual TestClient (sync) because it runs BackgroundTasks immediately
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "NutriSnap API" in response.json()["message"]


def test_predict_ingestion(client, tmp_path):
    # Create dummy image
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"dummy_image_data")

    with open(img_path, "rb") as f:
        # We need mock mode
        os.environ["NUTRISNAP_MOCK_CV"] = "true"
        response = client.post(
            "/predict", files={"file": ("test.jpg", f, "image/jpeg")}
        )

    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] in ["pending", "processing", "completed"]

    # Verify file exists
    upload_path = Path("datasets/uploads") / f"{data['job_id']}.jpg"
    assert upload_path.exists()

    # Cleanup dummy upload
    if upload_path.exists():
        upload_path.unlink()


def test_get_result_not_found(client):
    response = client.get("/result/non_existent_id")
    assert response.status_code == 404


def test_end_to_end_polling(client, tmp_path):
    os.environ["NUTRISNAP_MOCK_CV"] = "true"

    from unittest.mock import patch

    from nutrisnap.verification.api_fallback import FallbackResult

    mock_result = FallbackResult(
        calories=1000.0, protein=20.0, carbs=50.0, fat=15.0, source="cv_model"
    )

    with patch(
        "nutrisnap.verification.api_fallback.GeminiFallback.verify",
        return_value=mock_result,
    ):
        img_path = tmp_path / "polling_test.jpg"

        # Create valid dummy image
        import cv2
        import numpy as np

        dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
        _, buffer = cv2.imencode(".jpg", dummy_img)
        img_path.write_bytes(buffer.tobytes())

        with open(img_path, "rb") as f:
            resp = client.post(
                "/predict", files={"file": ("test.jpg", f, "image/jpeg")}
            )

        job_id = resp.json()["job_id"]

    # Poll
    # Since TestClient runs background tasks synchronous, it might already be done
    import time

    for i in range(30):
        resp = client.get(f"/result/{job_id}")
        data = resp.json()
        print(f"DEBUG: Poll {i}, status: {data['status']}")
        if data["status"] == "completed":
            assert data["result"]["calories"] == 1000.0
            return
        time.sleep(1.0)

    pytest.fail(
        f"Job {job_id} did not complete. Last status: {data['status']}. Error: {data.get('error')}"
    )
