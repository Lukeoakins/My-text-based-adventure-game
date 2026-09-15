import asyncio
from websockets.asyncio.server import serve

connected = {}


async def broadcast(text):
    for websocket in list(connected):
        await websocket.send(text)


async def handler(websocket):
    await websocket.send("What is your name?")
    name = await websocket.recv()

    connected[websocket] = name
    await broadcast(f"{name} has arrived")
    try:
        async for message in websocket:
            await broadcast(f"{name} says: {message}")
    finally:
        del connected[websocket]
        await broadcast(f"{name} has left the realm")


async def main():
    async with serve(handler, "localhost", 8765):
        print("listening on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()


asyncio.run(main())