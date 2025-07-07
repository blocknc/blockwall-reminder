# app.py
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
import os
import json
import threading
from store import load_users, save_users, mark_done, is_done, get_display_name, reset_status
from slack import send_modal, send_message, notify_admin_of_done
from tasks import daily_check
from datetime import datetime

app = Flask(__name__)
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
signature_verifier = SignatureVerifier(os.environ['SLACK_SIGNING_SECRET'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

@app.route("/slack/command", methods=["POST"])
def slack_command():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request signature", 403)

    data = request.form
    command = data.get("command")
    text = data.get("text")
    user_id = data.get("user_id")

    threading.Thread(target=handle_command_async, args=(command, text, user_id)).start()
    return make_response("Processing...", 200)

@app.route("/slack/interact", methods=["POST"])
def slack_interact():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    payload = json.loads(request.form["payload"])
    print("[Slack Interact] Payload:", json.dumps(payload, indent=2))

    if payload["type"] == "view_submission" and payload["view"]["callback_id"] == "upload_done_modal":
        user_id = payload["user"]["id"]
        comment = payload["view"]["state"]["upload_comment"]["comment_input"].get("value")
        mark_done(user_id)
        notify_admin_of_done(user_id, comment)
        return make_response("", 200)

    elif payload["type"] == "block_actions":
        action_id = payload["actions"][0]["action_id"]
        print(f"[Slack Interact] Block Action Triggered: {action_id}")
        if action_id == "open_reminder_modal":
            send_modal(payload["trigger_id"])
        return make_response("", 200)

    return make_response("", 200)

def handle_command_async(command, text, sender_id):
    args = text.split()
    if not args:
        send_message(sender_id, "❗ Bitte gib einen Befehl ein: add/remove/list/reset/run/status")
        return

    cmd = args[0]
    if cmd == 'add':
        if len(args) < 2:
            send_message(sender_id, "❗ Bitte gib einen Benutzer an: /reminder add @username")
            return
        user_arg = args[1].replace('@', '').replace('<@', '').replace('>', '').replace('!', '')
        try:
            all_users = client.users_list()
            match = next((u for u in all_users['members'] if u['name'] == user_arg or u['profile'].get('display_name') == user_arg or u['profile'].get('real_name') == user_arg), None)
            if not match:
                send_message(sender_id, f"❌ Konnte keinen Slack-User finden: {user_arg}")
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
            send_message(sender_id, f"✅ User {display_name} {'aktualisiert' if found else 'hinzugefügt'}.")
        except Exception as e:
            send_message(sender_id, f"❌ Fehler beim Hinzufügen: {str(e)}")

    elif cmd == 'remove':
        if len(args) < 2:
            send_message(sender_id, "❗ Bitte gib einen Benutzer an: /reminder remove @username")
            return
        user_tag = args[1].replace('@', '').replace('<@', '').replace('>', '').replace('!', '')
        users = load_users()
        all_users = client.users_list()
        match = next((u for u in all_users['members'] if u['name'] == user_tag or u['profile'].get('display_name') == user_tag or u['profile'].get('real_name') == user_tag), None)
        if not match:
            send_message(sender_id, f"❌ Konnte keinen Slack-User finden: {user_tag}")
            return
        slack_id = match["id"]
        filtered = [u for u in users if u["id"] != slack_id]
        if len(filtered) < len(users):
            save_users(filtered)
            send_message(sender_id, f"✅ User entfernt.")
        else:
            send_message(sender_id, f"⚠️ User nicht gefunden.")

    elif cmd == 'list':
        users = load_users()
        if not users:
            send_message(sender_id, "🔍 Keine Nutzer gefunden.")
        else:
            lines = [f"• {u['name']} ({u['id']})" for u in users]
            send_message(sender_id, "👥 *Aktive Reminder-User:*\n" + "\n".join(lines))

    elif cmd == 'status':
        users = load_users()
        if not users:
            send_message(sender_id, "📭 Keine Nutzer eingetragen.")
        else:
            lines = []
            for u in users:
                status = "✅ Done" if is_done(u['id']) else "🔴 Pending"
                lines.append(f"• {u['name']} ({u['id']}) – {status}")
            send_message(sender_id, "📊 *Status aller Nutzer:*\n" + "\n".join(lines))

    elif cmd == 'reset':
        reset_status()
        send_message(sender_id, "🧹 Status aller Nutzer zurückgesetzt.")

    elif cmd == 'run':
        daily_check(force=True)
        send_message(sender_id, "✅ Reminder-Logik manuell ausgeführt.")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
