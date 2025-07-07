# slack.py
import os
from slack_sdk import WebClient
from store import is_done

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

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
        },
        {
            "type": "input",
            "block_id": "upload_comment",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": "Optional comment (e.g., what is missing and why)"
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "comment_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "e.g., Expenses for travel, hotel, invoices..."
                }
            }
        }
    ]
}

def send_modal(trigger_id):
    client.views_open(trigger_id=trigger_id, view=REMINDER_MODAL)

def send_message(user_id, text, blocks=None):
    if blocks:
        client.chat_postMessage(channel=user_id, text=text, blocks=blocks)
    else:
        client.chat_postMessage(channel=user_id, text=text)

def notify_admin_of_done(user_id, comment=None):
    if not is_done(user_id):
        message = f"✅ <@{user_id}> has marked their receipts as done."
        if comment:
            message += f"\n📎 Comment: {comment}"
        client.chat_postMessage(channel=ADMIN_USER_ID, text=message)
