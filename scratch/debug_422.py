import asyncio
import httpx
import cv2
import numpy as np
import os
from nutrisnap.api.main import app, get_store, get_worker
from nutrisnap.api.store import ResultStore
from nutrisnap.api.worker import JobWorker

async def main():
    store = ResultStore(db_path="debug_nutrisnap.db")
    await store.initialize()
    worker = JobWorker(store)
    
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_worker] = lambda: worker
    
    dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy_img)
    img_bytes = buffer.tobytes()
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/predict",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.json()}")

if __name__ == "__main__":
    os.environ["NUTRISNAP_MOCK_CV"] = "true"
    asyncio.run(main())
