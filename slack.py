# slack.py
import os
from slack_sdk import WebClient

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

REMINDER_MODAL = {
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
                    "Hi there! 👋\n\nPlease remember to upload all your receipts for last month."
                    "\nClick *Done* after you've uploaded them."
                )
            }
        }
    ]
}

def send_modal(trigger_id):
    client.views_open(trigger_id=trigger_id, view=REMINDER_MODAL)

def send_message(user_id, text):
    client.chat_postMessage(channel=user_id, text=text)
