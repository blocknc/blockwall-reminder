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

def load_users():
    with open(USER_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def is_done(user_id):
    user_id = user_id.replace("@", "")
    with open(STATUS_FILE) as f:
        data = json.load(f)
    return str(data.get(user_id)) == "True"

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
