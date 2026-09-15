import asyncio
from websockets.asyncio.client import connect


async def main():
    async with connect("ws://localhost:8765") as websocket:
        await websocket.send("hello")
        reply = await websocket.recv()
        print(reply)


asyncio.run(main())