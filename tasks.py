# tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from store import load_users, is_done, save_users, mark_done
from slack import send_message, send_modal
from slack_sdk import WebClient
import os
import json
from flask import request, make_response

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

scheduler = BackgroundScheduler()

ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")  # must be set in .env

def daily_check():
    today = datetime.today().day
    if today > 4:
        return

    users = load_users()
    for user_id in users:
        if is_done(user_id):
            continue

        if today == 1:
            client.views_open(trigger_id=get_trigger_id(user_id), view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "Upload Reminder"},
                "close": {"type": "plain_text", "text": "Close"},
                "submit": {"type": "plain_text", "text": "Done"},
                "callback_id": "upload_done_modal",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "Hi! 👋 Just a monthly reminder to upload your receipts."
                            )
                        }
                    }
                ]
            })
        elif today in [2, 3]:
            send_message(user_id, "📌 Reminder: Don't forget to upload your receipts. Click Done in the reminder modal!")
        elif today == 4:
            send_message(user_id, "⚠️ Final notice: Upload your receipts today or you'll miss the deadline!")

    send_admin_status(users)

def get_trigger_id(user_id):
    res = client.chat_postMessage(channel=user_id, text="Managing reminders...")
    return res['message']['ts']

def send_admin_status(users):
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*User Upload Status*"}
        },
        {"type": "divider"}
    ]
    for user_id in users:
        try:
            info = client.users_info(user=user_id)
            display_name = info['user']['profile']['display_name'] or info['user']['real_name']
        except:
            display_name = user_id
        status = "✅ Done" if is_done(user_id) else "🕓 Pending"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{display_name}* (<@{user_id}>) – {status}"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Remove"},
                "style": "danger",
                "value": user_id,
                "action_id": "remove_user"
            }
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "input",
        "block_id": "add_user_input",
        "element": {
            "type": "plain_text_input",
            "action_id": "new_user_id",
            "placeholder": {"type": "plain_text", "text": "Enter @username or Slack ID"}
        },
        "label": {"type": "plain_text", "text": "Add a user by Slack @username or ID"}
    })
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Submit"},
                "action_id": "submit_add_user"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Refresh Status"},
                "action_id": "refresh_status"
            }
        ]
    })

    client.views_open(trigger_id=get_trigger_id(ADMIN_USER_ID), view={
        "type": "modal",
        "title": {"type": "plain_text", "text": "User Status"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": blocks,
        "callback_id": "admin_status_view"
    })

def handle_admin_interaction(payload):
    action = payload['actions'][0]
    action_id = action['action_id']
    users = load_users()

    if action_id == "remove_user":
        user_id = action['value']
        if user_id in users:
            users.remove(user_id)
            save_users(users)
        send_admin_status(users)

    elif action_id == "submit_add_user":
        state = payload.get("view", {}).get("state", {})
        blocks = state.get("values", {})
        input_val = None
        for b in blocks.values():
            input_val = b.get("new_user_id", {}).get("value")
            if input_val:
                break
        if input_val:
            input_val = input_val.strip().replace("<@", "").replace(">", "")
            try:
                result = client.users_lookupByEmail(email=input_val) if "@" in input_val else client.users_info(user=input_val)
                user_id = result['user']['id']
                if user_id not in users:
                    users.append(user_id)
                    save_users(users)
            except:
                pass
        send_admin_status(users)

    elif action_id == "refresh_status":
        send_admin_status(users)

def start_scheduler():
    scheduler.add_job(daily_check, 'cron', hour=9)  # runs daily at 9am
    scheduler.start()
