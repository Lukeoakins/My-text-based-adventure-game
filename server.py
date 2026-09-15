import asyncio
from websockets.asyncio.server import serve

connected = {}
rooms = {
    "camp": {
        "name": "The camp",
        "description": "A safe spot to sleep, with a fire",
        "exits": {"river": "lake_shack", "north": "treeline"}
    },
    "lake_shack": {
        "name": "The lake shack",
        "description": "A humble wooden shack, resting on top of a bank by the lake",
        "exits" : {"river": "camp"}
    },
    "treeline": {
        "name": "The treeline",
        "description": "a sudden, unnatural cuttoff from the once dense forest",
        "exits": {"south": "camp"}
    }
         }

async def broadcast(text):
    for websocket in list(connected):
        await websocket.send(text)


async def handler(websocket):
    await websocket.send("What is your name?")
    name = await websocket.recv()

    connected[websocket] = {"name" : name, "location" : "camp"}
    await broadcast(f"{name} has arrived")
    try:
        async for message in websocket:
            parts = message.strip().split(" ", 1)
            command = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ""

            if command == "say":
                await broadcast(f"{name} says: {rest}")
            elif command == "who":
                names = ", ".join(player["name"] for player in connected.values())
                await websocket.send(f"{names} are currently online")
            elif command == "quit":
                await websocket.send("wake up")
                await websocket.close()
            elif command == "look":
                player = connected[websocket]
                room = rooms[player["location"]]
                exits = ", ".join(room["exits"])
                text = (f"{room['name']}\n\n"
                        f"{room['description']}\n\n"
                        f"exits: {exits}")
                await websocket.send(text)
            else:
                await websocket.send(f"the command {command} does not exist")
    finally:
        del connected[websocket]
        await broadcast(f"{name} has left the realm")


async def main():
    async with serve(handler, "localhost", 8765):
        print("listening on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()


asyncio.run(main())