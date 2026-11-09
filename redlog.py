import json
import sqlite3

db = sqlite3.connect("grimoire.db")

for row in db.execute("SELECT id, timestamp, actor, verb, payload FROM events ORDER BY id"):
    id, timestamp, actor, verb, payload = row
    print(f"{id:4}  {timestamp[11:19]}  {actor:10}  {verb:8}  {json.loads(payload)}")