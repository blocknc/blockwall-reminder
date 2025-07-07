# app.py
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
import os
import json
import threading
from store import load_users, save_users, mark_done, is_done, reset_status, get_display_name
from slack import send_modal, send_message
from datetime import datetime

app = Flask(__name__)

# Slack command endpoint
@app.route("/slack/command", methods=["POST"])
def slack_command():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request signature", 403)

    data = request.form
    command = data.get("command")
    text = data.get("text")
    user_id = data.get("user_id")

    threading.Thread(target=handle_command_async, args=(command, text, user_id)).start()
    return make_response("", 200)


# Optional startup validation for JSON files
try:
    users = load_users()
    if not isinstance(users, list):
        raise ValueError("users.json is not a list")
    for u in users:
        if not isinstance(u, dict) or "id" not in u or "name" not in u:
            raise ValueError("Invalid user entry")
except Exception as e:
    print(f"❌ Error loading users.json: {e}")
    with open("users.json", "w") as f:
        json.dump([], f)

try:
    with open("status.json") as f:
        status_data = json.load(f)
    if not isinstance(status_data, dict):
        raise ValueError("status.json is not a dict")
except Exception as e:
    print(f"❌ Error loading status.json: {e}")
    with open("status.json", "w") as f:
        json.dump({}, f)
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
signature_verifier = SignatureVerifier(os.environ['SLACK_SIGNING_SECRET'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

def handle_command_async(command, text, sender_id):
    args = text.split()
    if args[0] == 'add':
        user_arg = args[1].replace('@', '').replace('<@', '').replace('>', '').replace('!', '')
        try:
            all_users = client.users_list()
            match = next((u for u in all_users['members'] if u['id'] == user_arg or u['name'] == user_arg or u['profile'].get('display_name') == user_arg or u['profile'].get('real_name') == user_arg), None)
            if not match:
                send_message(sender_id, f"❌ Could not find a Slack user for: {user_arg}")
                return
            slack_id = match["id"]
            display_name = match["profile"].get("display_name") or match["profile"].get("real_name") or user_arg
            users = load_users()
            found = False
            for u in users:
                if u["id"] == slack_id:
                    u["name"] = display_name
                    found = True
            if not found:
                users.append({"id": slack_id, "name": display_name})
            save_users(users)
            send_message(sender_id, f"✅ User {display_name} {'updated' if found else 'added'}.")
        except:
            send_message(sender_id, f"❌ Failed to add user: {args[1]}")

    elif args[0] == 'remove':
        user_tag = args[1].replace('<@', '').replace('>', '').replace('!', '')
        users = load_users()
        filtered = [u for u in users if u["id"] != user_tag and u["name"] != user_tag]
        if len(filtered) < len(users):
            save_users(filtered)
            send_message(sender_id, f"✅ User removed.")
        else:
            send_message(sender_id, f"⚠️ User not found in list.")

    elif args[0] == 'list':
        users = load_users()
        user_list = '\n'.join([f"• {u['name']} ({u['id']})" for u in users])
