"""Boundary and edge-case tests for NutriSnap API."""
import pytest
import os
import cv2
import numpy as np
from fastapi.testclient import TestClient
from nutrisnap.api.main import app, get_store, get_worker
from nutrisnap.api.store import ResultStore
from nutrisnap.api.worker import JobWorker


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "boundary_nutrisnap.db"
    store = ResultStore(db_path=db_path)
    # Pre-initialize store for job creation
    import asyncio
    asyncio.run(store.initialize())
    
    worker = JobWorker(store)
    
    # Note: TestClient handles startup/lifespan events
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_worker] = lambda: worker
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_invalid_file_type(client):
    """Ensure non-image files are rejected at ingestion."""
    response = client.post(
        "/predict",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]


def test_corrupt_image_data(client):
    """Ensure corrupt image data is handled by the worker gracefully."""
    os.environ["NUTRISNAP_MOCK_CV"] = "true"
    # Submit 100 random bytes as an image
    response = client.post(
        "/predict",
        files={"file": ("corrupt.jpg", b"\x00" * 100, "image/jpeg")}
    )
    if response.status_code != 200:
        print(f"DEBUG: Response {response.status_code}, {response.json()}")
        
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Poll for result - should fail
    import time
    for _ in range(10):
        resp = client.get(f"/result/{job_id}")
        data = resp.json()
        if data["status"] == "failed":
            assert "Failed to decode image" in data["error"]
            return
        time.sleep(1)
        
    pytest.fail("Job did not reach failed state for corrupt image")


def test_large_image_handling(client):
    """Sanity check for larger images (within memory constraints)."""
    os.environ["NUTRISNAP_MOCK_CV"] = "true"
    # Create 4K black image
    large_img = np.zeros((2160, 3840, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", large_img)
    
    response = client.post(
        "/predict",
        files={"file": ("large.jpg", buffer.tobytes(), "image/jpeg")}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Poll for completion
    import time
    for _ in range(20):
        resp = client.get(f"/result/{job_id}")
        data = resp.json()
        if data["status"] == "completed":
            return
        time.sleep(1)
        
    pytest.fail("Large image job timed out or failed")
