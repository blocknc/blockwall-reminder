# store.py
import json
import os

USER_FILE = "users.json"
STATUS_FILE = "status.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "w") as f:
        json.dump({}, f)

# Cleanup invalid or malformed entries in status.json
with open(STATUS_FILE) as f:
    try:
        status_data = json.load(f)
    except json.JSONDecodeError:
        status_data = {}

if not isinstance(status_data, dict):
    status_data = {}
else:
    # keep only string keys and bool values
    status_data = {
        str(k).replace("@", ""): bool(v) if isinstance(v, bool) else False
        for k, v in status_data.items()
    }

with open(STATUS_FILE, "w") as f:
    json.dump(status_data, f)

def load_users():
    with open(USER_FILE) as f:
        raw = json.load(f)
    return [uid.replace("@", "") for uid in raw]

def save_users(users):
    cleaned = list({u.replace("@", "") for u in users})
    with open(USER_FILE, "w") as f:
        json.dump(cleaned, f)

def is_done(user_id):
    user_id = user_id.replace("@", "")
    with open(STATUS_FILE) as f:
        data = json.load(f)
    return data.get(user_id) is True

def mark_done(user_id):
    user_id = user_id.replace("@", "")
    with open(STATUS_FILE) as f:
        data = json.load(f)
    data[user_id] = True
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def reset_status():
    users = load_users()
    new_status = {uid.replace("@", ""): False for uid in users}
    with open(STATUS_FILE, "w") as f:
        json.dump(new_status, f)
