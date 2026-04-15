"""High-concurrency stress test for NutriSnap GPU Lock."""
import pytest
import asyncio
import os
import time
import httpx
import cv2
import numpy as np
from nutrisnap.api.main import app, get_store, get_worker
from nutrisnap.api.store import ResultStore
from nutrisnap.api.worker import JobWorker


@pytest.fixture
async def async_client(tmp_path):
    # Use a temp DB for tests
    db_path = tmp_path / "concurrent_nutrisnap.db"
    store = ResultStore(db_path=db_path)
    await store.initialize()
    
    # Create worker
    worker = JobWorker(store)
    
    # Override dependencies
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_worker] = lambda: worker
    
    # Use ASGITransport for async testing
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client, store
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_gpu_lock_serialization(async_client):
    client, store = async_client
    os.environ["NUTRISNAP_MOCK_CV"] = "true"
    
    # Create valid dummy image
    dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy_img)
    img_bytes = buffer.tobytes()
    
    num_jobs = 5
    print(f"\nSubmitting {num_jobs} concurrent jobs...")
    
    start_time = time.time()
    
    async def submit_job(i):
        resp = await client.post(
            "/predict",
            files={"file": (f"test_{i}.jpg", img_bytes, "image/jpeg")}
        )
        if resp.status_code != 200:
            print(f"FAILED JOB {i}: {resp.json()}")
        assert resp.status_code == 200
        return resp.json()["job_id"]

    # Submit all at once
    job_ids = await asyncio.gather(*[submit_job(i) for i in range(num_jobs)])
    
    # Poll until all complete
    completed_jobs = {}
    
    while len(completed_jobs) < num_jobs:
        if time.time() - start_time > 30:
             pytest.fail("Jobs timed out")
             
        for jid in job_ids:
            if jid in completed_jobs:
                continue
            resp = await client.get(f"/result/{jid}")
            data = resp.json()
            if data["status"] == "completed":
                completed_jobs[jid] = time.time()
        
        await asyncio.sleep(0.5)

    # Verification:
    # In mock mode, each job takes 0.5s + GPU Lock serialization.
    # Total time should be >= num_jobs * 0.5
    total_duration = time.time() - start_time
    print(f"Total duration for {num_jobs} serialized jobs: {total_duration:.2f}s")
    
    assert total_duration >= num_jobs * 0.45 
