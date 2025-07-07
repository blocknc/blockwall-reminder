# app.py
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
import os
import json
import threading
from store import load_users, save_users, mark_done, is_done, reset_status
from slack import send_modal, send_message, notify_admin_of_done
from datetime import datetime

app = Flask(__name__)
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
signature_verifier = SignatureVerifier(os.environ['SLACK_SIGNING_SECRET'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

def handle_command_async(command, text, user_id):
    args = text.split()
    if args[0] == 'add':
        user = args[1].replace('<@', '').replace('>', '')
        users = load_users()
        if user not in users:
            users.append(user)
            save_users(users)
            send_message(user_id, f"User <@{user}> added.")
    elif args[0] == 'remove':
        user = args[1].replace('<@', '').replace('>', '')
        users = load_users()
        if user in users:
            users.remove(user)
            save_users(users)
            send_message(user_id, f"User <@{user}> removed.")
    elif args[0] == 'list':
        users = load_users()
        user_list = ', '.join([f"<@{u}>" for u in users])
        send_message(user_id, f"Reminder list: {user_list}")
    elif args[0] == 'run':
        users = load_users()
        for uid in users:
            if is_done(uid):
                continue
            send_message(uid, "📌 *Monthly Receipt Reminder*\nPlease upload your receipts and click below when done.", [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Mark as Done"},
                    "action_id": "open_reminder_modal",
                    "value": uid
                }
            ])
        send_message(user_id, "Manual reminder check triggered.")
    elif args[0] == 'status':
        users = load_users()
        pending = [f"<@{u}>" for u in users if not is_done(u)]
        done = [f"<@{u}>" for u in users if is_done(u)]
        message = "📋 *Monthly Receipt Status Summary*\n"
        message += f"\n✅ Done: {', '.join(done) if done else 'None'}"
        message += f"\n🕓 Pending: {', '.join(pending) if pending else 'None'}"
        send_message(ADMIN_USER_ID, message)
    elif args[0] == 'reset':
        reset_status()
        send_message(user_id, "✅ All receipt statuses have been reset for a new month.")

@app.route('/slack/commands', methods=['POST'])
def slack_commands():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    data = request.form
    command = data.get('command')
    user_id = data.get('user_id')
    text = data.get('text')

    thread = threading.Thread(target=handle_command_async, args=(command, text, user_id))
    thread.start()

    return make_response("", 200)

@app.route('/slack/events', methods=['POST'])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    payload = request.json

    if "type" in payload:
        if payload["type"] == "url_verification":
            return make_response(payload["challenge"], 200)
        if payload["type"] == "event_callback":
            return make_response("", 200)

    return make_response("", 200)

@app.route('/slack/interact', methods=['POST'])
def slack_interact():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    payload = json.loads(request.form["payload"])
    user_id = payload["user"]["id"]

    if payload["type"] == "view_submission":
        comment = None
        try:
            comment = payload["view"]["state"]["values"].get("upload_comment", {}).get("comment_input", {}).get("value")
        except:
            comment = None

        notify_admin_of_done(user_id, comment)
        mark_done(user_id)
        send_message(user_id, "✅ Thank you! Your receipt status has been marked as done.")
        return make_response("", 200)

    elif payload["type"] == "block_actions":
        action = payload['actions'][0]
        if action['action_id'] == "open_reminder_modal":
            if is_done(user_id):
                send_message(user_id, "✅ You’ve already marked your receipts as done this month.")
            else:
                trigger_id = payload["trigger_id"]
                send_modal(trigger_id)
        else:
            handle_admin_interaction(payload)
        return make_response("", 200)

    return make_response("", 200)

if __name__ == '__main__':
    app.run(port=3000)
