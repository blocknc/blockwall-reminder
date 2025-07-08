# store.py
import json
import os

USERS_FILE = "data/users.json"
STATUS_FILE = "data/status.json"

os.makedirs("data", exist_ok=True)

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def mark_done(user_id, comment=None):
    status = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            status = json.load(f)
    status[user_id] = {"done": True, "comment": comment or ""}
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def is_done(user_id):
    if not os.path.exists(STATUS_FILE):
        return False
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    entry = status.get(user_id)
    if isinstance(entry, dict):
        return entry.get("done", False)
    return bool(entry)

def get_comment(user_id):
    if not os.path.exists(STATUS_FILE):
        return None
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    entry = status.get(user_id)
    if isinstance(entry, dict):
        return entry.get("comment")
    return None

def reset_status():
    with open(STATUS_FILE, "w") as f:
        json.dump({}, f)

    users = load_users()
    for u in users:
        if "ts" in u:
            del u["ts"]
    save_users(users)

def reset_status_for_user(user_id):
    if not os.path.exists(STATUS_FILE):
        return
    with open(STATUS_FILE, "r") as f:
        status = json.load(f)
    if user_id in status:
        del status[user_id]
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def get_display_name(user_id):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            return u.get("name")
    return user_id

def save_message_ts(user_id, ts):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            u["ts"] = ts
            break
    save_users(users)

def get_message_ts(user_id):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            return u.get("ts")
    return None

def clear_message_ts(user_id):
    users = load_users()
    for u in users:
        if u["id"] == user_id and "ts" in u:
            del u["ts"]
    save_users(users)
