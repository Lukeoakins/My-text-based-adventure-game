# The Living Grimoire
 
A multiplayer text adventure server written in Python. Players connect from a browser, explore a small world, and pick up, drop and trade items with each other in real time.
 
Built with **async WebSockets** so one server process can handle many players at once, with every action recorded in a **SQLite event log**.

 
## Features
 
- **Real-time multiplayer:** see other players arrive, leave, talk and trade as it happens
- **Rooms and movement:** explore connected locations (the camp, the lake shack, the treeline)
- **Items and inventory:** pick up, drop and give items, with a weight-based carry limit
- **Event log:** every action (arriving, moving, talking, trading) is stored in SQLite with a timestamp
- **Browser client:** a simple HTML/JavaScript page that talks to the server over WebSockets
## Commands
 
| Command | What it does |
|---|---|
| `look` | Describe the current room, its exits and any items on the ground |
| `go <exit>` | Move through an exit, e.g. `go north` |
| `say <message>` | Talk to every player online |
| `take <item>` | Pick up an item in the room |
| `drop <item>` | Drop an item you are carrying |
| `give <item> to <player>` | Hand an item to another player in the same room |
| `inventory` | See what you are carrying and how heavy your load is |
| `who` | List everyone online |
| `quit` | Leave the game |
 
## Running it
 
Requires **Python 3.12+**.
 
```bash
# set up a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
 
# install the one dependency
pip install websockets
 
# start the server
python server.py
```
 
You should see `listening on ws://localhost:8765`. Then open `client.html` in a browser, enter a name, and start typing commands. Open a second browser window to play as another player.
 
## How it works
 
- **`server.py`** runs an `asyncio` WebSocket server. Each connected player gets their own handler, and `await` lets the server serve everyone without a thread per connection.
- Connected players are kept in a dictionary mapping each socket to that player's state (name and location). Helper functions use it to message everyone, or just the players in one room.
- Every action is written to an `events` table using **parameterised queries**, so player input can never be run as SQL.
- Carried weight is **calculated from the items** rather than stored, so it can never fall out of sync.
- **`client.html` / `client.js`** open a WebSocket to the server, send what you type, and print whatever the server pushes back.
## What I'd improve next
 
- **Persist the world.** Rooms and items live in memory and reset when the server restarts; only the event log survives.
- **Unique player IDs.** Items are currently held by player name, so two players with the same name would clash.
- **Non-blocking database writes.** `sqlite3` is a blocking call inside async code; at larger scale I'd move to PostgreSQL with an async driver such as `asyncpg`.
- **More world.** More rooms, items, and actions that use them.
 
