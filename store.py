# store.py
import json
import os
from slack_sdk import WebClient

USER_FILE = "users.json"
STATUS_FILE = "status.json"

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

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
        return json.load(f)

def get_display_name(user_id):
    try:
        user_info = client.users_info(user=user_id)
        profile = user_info.get("user", {}).get("profile", {})
        return profile.get("display_name") or profile.get("real_name") or user_id
    except:
        return user_id

def save_users(users):
    cleaned = []
    seen = set()
    for u in users:
        uid = u["id"].replace("@", "")
        if uid not in seen:
            cleaned.append({"id": uid, "name": u["name"]})
            seen.add(uid)
    with open(USER_FILE, "w") as f:
        json.dump(cleaned, f)

def is_done(user_id):
    user_id = user_id.replace("@", "")
    with open(STATUS_FILE) as f:
        data = json.load(f)
    return data.get(user_id, False)

def mark_done(user_id):
    user_id = user_id.replace("@", "")
    with open(STATUS_FILE) as f:
        data = json.load(f)
    data[user_id] = True
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def reset_status():
    users = load_users()
    new_status = {u["id"].replace("@", ""): False for u in users}
    with open(STATUS_FILE, "w") as f:
        json.dump(new_status, f)
