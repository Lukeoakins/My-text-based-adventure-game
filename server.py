import asyncio 
from websockets.asyncio.server import serve

async def handler(websocket):
    print("A player has joined")

    async for message in websocket:
        print(f"received: {message}")
        await websocket.send(f"you said: {message}")

    print("player disconnected")

async def main():
    async with serve(handler, "localhost", 8765):
        print("listening on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()

asyncio.run(main())