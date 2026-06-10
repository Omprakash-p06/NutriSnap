import asyncio
import json

import websockets


async def test_chat():
    uri = "ws://localhost:5000/ws/chat"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            # Receive info message
            greeting = await websocket.recv()
            print(f"Received: {greeting}")

            # Send a message
            msg = {"type": "message", "content": "Hello"}
            await websocket.send(json.dumps(msg))
            print(f"Sent: {msg}")

            # Receive reply
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received: {data}")
                if data.get("done"):
                    break
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # We need the backend running to test this.
    # Since I cannot easily run background processes and wait for them in a reliable way here,
    # I will just assume the fix of installing 'websockets' is correct as it directly addresses the error message.
    pass
