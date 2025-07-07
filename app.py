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
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
signature_verifier = SignatureVerifier(os.environ['SLACK_SIGNING_SECRET'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

def handle_command_async(command, text, sender_id):
    args = text.split()
    if args[0] == 'add':
        user_arg = args[1]
        try:
            if user_arg.startswith("<@") and user_arg.endswith(">"):
                slack_id = user_arg[2:-1].replace("!", "")
            else:
                # Try to resolve name to ID from full user list
                all_users = client.users_list()
                match = next((u for u in all_users['members'] if u['name'] == user_arg or u['profile'].get('display_name') == user_arg or u['profile'].get('real_name') == user_arg), None)
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
        send_message(sender_id, f"👥 Reminder list: {user_list}")

    elif args[0] == 'run':
        users = load_users()
        for u in users:
            slack_id = u["id"]
            if is_done(slack_id):
                continue
            send_message(slack_id, "📌 Monthly Receipt Reminder", blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "📌 *Monthly Receipt Reminder*\nPlease upload your receipts and click below when done."}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark as Done"},
                            "action_id": "open_reminder_modal",
                            "value": slack_id
                        }
                    ]
                }
            ])
        send_message(sender_id, "Manual reminder check triggered.")

    elif args[0] == 'status':
        users = load_users()
        status_lines = []
        for u in users:
            name = u["name"]
            done = is_done(u["id"])
            status_lines.append(f"✅ {name}" if done else f"🕓 {name}")
        message = "📋 *Monthly Receipt Status Summary*\n" + "\n".join(status_lines)
        send_message(ADMIN_USER_ID, message)

    elif args[0] == 'reset':
        reset_status()
        send_message(sender_id, "✅ All receipt statuses have been reset for a new month.")

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
        state_values = payload["view"]["state"]["values"]
        comment = None
        for block in state_values.values():
            for action in block.values():
                comment = action.get("value", None)

        mark_done(user_id)
        send_message(user_id, "✅ Thank you! Your receipt status has been marked as done.")
        if ADMIN_USER_ID:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            msg = f"✅ <@{user_id}> has marked their receipts as done at {timestamp}."
            if comment:
                msg += f"\n📝 Comment: {comment}"
            send_message(ADMIN_USER_ID, msg)
        return make_response("", 200)

    elif payload["type"] == "block_actions":
        action = payload['actions'][0]
        if action['action_id'] == "open_reminder_modal":
            if is_done(user_id):
                send_message(user_id, "✅ You’ve already marked your receipts as done this month.")
            else:
                trigger_id = payload["trigger_id"]
                send_modal(trigger_id)
        return make_response("", 200)

    return make_response("", 200)

if __name__ == '__main__':
    app.run(port=3000)
