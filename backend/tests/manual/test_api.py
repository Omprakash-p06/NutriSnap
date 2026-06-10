import time

import requests


def test_api():
    url = "http://127.0.0.1:5000/predict/"
    print(f"Testing API endpoint: {url}")

    # We will just pass a dummy valid JPEG
    image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x02\x01\x01\x01\x01\x01\x02\x01\x01\x01\x02\x02\x02\x02\x02\x04\x03\x02\x02\x02\x02\x05\x04\x04\x03\x04\x06\x05\x06\x06\x06\x05\x06\x06\x06\x07\t\x08\x06\x07\t\x07\x06\x06\x08\x0b\x08\t\n\n\n\n\n\x06\x08\x0b\x0c\x0b\n\x0c\t\n\n\n\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xd2\xcf\x20\xff\xd9"
    files = {"file": ("test.jpg", image_data, "image/jpeg")}

    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            job_id = response.json().get("job_id")
            if job_id:
                print(f"Job started successfully: {job_id}. Polling...")
                while True:
                    status_url = f"http://127.0.0.1:5000/predict/status/{job_id}"
                    status_res = requests.get(status_url)
                    if status_res.status_code == 403:
                        print(
                            "Got 403 Forbidden. This is expected because we don't have an auth token in this test script."
                        )
                        break
                    print(status_res.json())
                    if status_res.json().get("status") in ["done", "failed"]:
                        break
                    time.sleep(2)
    except Exception as e:
        print(f"Failed to connect: {e}")


if __name__ == "__main__":
    test_api()
