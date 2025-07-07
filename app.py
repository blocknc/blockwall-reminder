# app.py (for Render web service only – no scheduler)
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
import os
import json
from store import load_users, save_users, mark_done, is_done
from slack import send_modal, send_message
from tasks import handle_admin_interaction
from tasks import start_scheduler

app = Flask(__name__)
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
signature_verifier = SignatureVerifier(os.environ['SLACK_SIGNING_SECRET'])

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

@app.route('/slack/commands', methods=['POST'])
def slack_commands():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    data = request.form
    command = data.get('command')
    user_id = data.get('user_id')
    text = data.get('text')

    if command == '/reminder':
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

    return make_response("", 200)

@app.route('/slack/interact', methods=['POST'])
def slack_interact():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)

    payload = json.loads(request.form["payload"])
    user_id = payload["user"]["id"]

    if payload["type"] == "view_submission":
        mark_done(user_id)
        return make_response("", 200)

    elif payload["type"] == "block_actions":
        handle_admin_interaction(payload)
        return make_response("", 200)

    return make_response("", 200)

if __name__ == '__main__':
    start_scheduler()
    app.run(port=3000)
