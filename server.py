import asyncio
from websockets.asyncio.server import serve
import json
import sqlite3
from datetime import datetime, timezone

db = sqlite3.connect("grimoire.db")
db.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT NOT NULL,
        actor     TEXT,
        verb      TEXT NOT NULL,
        payload   TEXT
    )
""")
db.commit()

connected = {}
items = [
    {"id": 1, "name": "iron ore",  "weight": 12, "location": "camp",     "holder": None},
    {"id": 2, "name": "iron ore",  "weight": 12, "location": "camp",     "holder": None},
    {"id": 3, "name": "hand axe",  "weight": 3,  "location": "treeline", "holder": None},
]
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

CARRY_LIMIT = 40
def load_description(weight):
    if weight == 0:
        return "You are carrying nothing."
    if weight < CARRY_LIMIT * 0.3:
        return "You are carrying a slight load"
    if weight < CARRY_LIMIT * 0.6:
        return "you are carrying a decent load"
    if weight < CARRY_LIMIT * 0.9:
        return "you are carrying a severe load"
    return "trying to move even a step is extremely uncomfortable"

def log(actor, verb, **payload):
    db.execute(
        "INSERT INTO events (timestamp, actor, verb, payload) VALUES (?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            actor,
            verb,
            json.dumps(payload),
        ),
    )
    db.commit()

async def broadcast(text):
    for websocket in list(connected):
        await websocket.send(text)

def describe(player):
    room = rooms[player["location"]]
    exits = ", ".join(room["exits"])

    text = (
        f"{room['name']}\n\n"
        f"{room['description']}\n\n"
        f"Exits: {exits}"
    )

    here = items_in_room(player["location"])
    if here:
        names = ", ".join(item["name"] for item in here)
        text += f"\n\nOn the ground: {names}"

    return text

async def to_room(location, text, exclude=None):
    for websocket, player in list(connected.items()):
        if player["location"] == location and websocket is not exclude:
            await websocket.send(text)

def find_player(name, location):
    for websocket, player in connected.items():
        if player["location"] == location and name.lower() in player["name"].lower():
            return websocket, player
    return None, None

def carried_weight(name):
    return sum(item["weight"] for item in items_held_by(name))

def items_in_room(location):
    return[item for item in items if item["location"] == location]

def items_held_by(name):
    return [item for item in items if item["holder"] == name]

def find_item(name, candidates):
    for item in candidates:
        if name.lower() in item["name"].lower():
            return item
    return None

async def handler(websocket):
    await websocket.send("What is your name?")
    name = await websocket.recv()

    connected[websocket] = {"name" : name, "location" : "camp"}
    player = connected[websocket]
    log(name, "arrive", location="camp")
    await broadcast(f"{name} has arrived")
    try:
        async for message in websocket:
            parts = message.strip().split(" ", 1)
            command = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ""

            if command == "say":
                log(player["name"], "say", text=rest, location=player["location"])
                await broadcast(f"{name} says: {rest}")
            elif command == "who":
                names = ", ".join(player["name"] for player in connected.values())
                await websocket.send(f"{names} are currently online")
            elif command == "quit":
                await websocket.send("wake up")
                await websocket.close()
            elif command == "look":
                await websocket.send(describe(connected[websocket]))
            elif command == "go":
                here = player["location"]
                direction = rest.lower()

                if direction not in rooms[here]["exits"]:
                    await websocket.send("there is no obvious path")
                else:
                    destination = rooms[here]["exits"][direction]
                    await to_room(here, f"{player['name']} leaves, {direction}.", exclude = websocket)
                    player["location"] = destination
                    log(player["name"], "go", direction=direction, frm=here, to=destination)
                    await to_room(destination, f"{player['name']} arrives.", exclude = websocket)
                    await websocket.send(describe(player))
            elif command == "take":
                match = find_item(rest, items_in_room(player["location"]))
                if match is None:
                    await websocket.send(f"There is no {rest} here")
                elif carried_weight(player["name"]) + match["weight"] > CARRY_LIMIT:
                    await websocket.send("You cannot lift it with what you are already carrying.")
                else:
                    match["location"] = None
                    match["holder"] = player["name"]
                    log(player["name"], "take", item=match["id"], location=player["location"])
                    await websocket.send(f"you have picked up the {match['name']}")
                    await to_room(player["location"], f"{player['name']} picked up {match['name']}.", exclude = websocket)
            elif command == "drop":
                match = find_item(rest, items_held_by(player["name"]))
                if match is None:
                    await websocket.send(f"you do not have any {rest}")
                else:
                    match["holder"] = None
                    match["location"] = player["location"]
                    log(player["name"], "drop", item=match["id"], location=player["location"])
                    await websocket.send(f"you have dropped {match['name']}")
                    await to_room(player["location"], f"{player['name']} has dropped {match['name']}.", exclude = websocket)
            elif command == "inventory":
                carried = items_held_by(player['name'])
                if not carried:
                    await websocket.send("you are not carrying anything")
                else:
                    names = ", ".join(item["name"] for item in carried)
                    load = load_description(carried_weight(player["name"]))
                    await websocket.send(f"You are carrying: {names}\n{load}")
            elif command == "give":
                if " to " not in rest:
                    await websocket.send("give what, to whom?")
                else:
                    thing, target_name = rest.split(" to ", 1)
                    match = find_item(thing, items_held_by(player["name"]))
                    target_socket, target = find_player(target_name, player["location"])
                    if match is None:
                        await websocket.send(f"you do not have {rest}")
                    elif target is None:
                        await websocket.send(f"there is no player going by {target_name}")
                    elif target is player:
                        await websocket.send("you cannot send it to yourself")
                    elif carried_weight(target["name"]) + match["weight"] > CARRY_LIMIT:
                        await websocket.send(f"{target['name']} is carrying too much!")
                    else:
                        match["holder"] = target["name"]
                        log(player["name"], "give", item=match["id"], to=target["name"])
                        await websocket.send(f"you have given a {match["name"]} to {target["name"]}")
                        await target_socket.send(f"{player['name']} gives you the {match['name']}.")
                        await to_room(player["location"], f"{player["name"]} has given {target["name"]} {match["name"]}")
                    
            else:
                await websocket.send(f"the command {command} does not exist")
    finally:
        log(player["name"], "leave", location=player["location"])
        del connected[websocket]
        await broadcast(f"{name} has left the realm")


async def main():
    async with serve(handler, "localhost", 8765):
        print("listening on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()


asyncio.run(main())