# store.py
import json
from datetime import datetime

FILE_USERS = 'users.json'
FILE_STATUS = 'status.json'


def load_users():
    try:
        with open(FILE_USERS, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open(FILE_USERS, 'w') as f:
        json.dump(users, f)

def mark_done(user_id):
    status = load_status()
    month = current_month()
    if month not in status:
        status[month] = []
    if user_id not in status[month]:
        status[month].append(user_id)
    save_status(status)

def is_done(user_id):
    status = load_status()
    return user_id in status.get(current_month(), [])

def load_status():
    try:
        with open(FILE_STATUS, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_status(data):
    with open(FILE_STATUS, 'w') as f:
        json.dump(data, f)

def current_month():
    return datetime.now().strftime('%Y-%m')
