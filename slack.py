# slack.py
import os
from slack_sdk import WebClient
from store import is_done, get_comment, load_users, mark_done, save_message_ts, get_message_ts, clear_message_ts

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

REMINDER_MODAL = {
    "type": "modal",
    "title": {"type": "plain_text", "text": "Reminder"},
    "close": {"type": "plain_text", "text": "Close"},
    "submit": {"type": "plain_text", "text": "Done"},
    "callback_id": "upload_done_modal",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "📥 *Request*\nPlease upload your AMEX receipts for last month.\nClick *Done* once you've completed the upload."
                )
            }
        },
        {
            "type": "input",
            "block_id": "upload_comment",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": "Comment (e.g. missing receipts)"
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "comment_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "e.g. hotel invoice still missing ..."
                }
            }
        }
    ]
}

def send_modal(trigger_id):
    client.views_open(trigger_id=trigger_id, view=REMINDER_MODAL)

def send_message(user_id, text, blocks=None):
    try:
        if blocks:
            client.chat_postMessage(channel=user_id, text=text, blocks=blocks)
        else:
            client.chat_postMessage(channel=user_id, text=text)
    except Exception as e:
        print(f"❌ Failed to send message to {user_id}: {e}")

def send_reminder(user_id):
    if is_done(user_id):
        return
    try:
        result = client.chat_postMessage(
            channel=user_id,
            text="Reminder",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📌 *Monthly Receipt Reminder*\nPlease upload your receipts and click below when done."
                    }
                },
                {
                    "type": "actions",
                    "block_id": "reminder_action",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark as Done"},
                            "action_id": "open_reminder_modal"
                        }
                    ]
                }
            ]
        )
        save_message_ts(user_id, result["ts"])
    except Exception as e:
        print(f"❌ Failed to send reminder to {user_id}: {e}")

def update_reminder(user_id):
    ts = get_message_ts(user_id)
    if not ts:
        return
    try:
        client.chat_update(
            channel=user_id,
            ts=ts,
            text="✅ Already done",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *Thanks!* Your receipt upload has been marked as Done."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "_You can no longer interact with this reminder._"
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"❌ Failed to update message for {user_id}: {e}")

def notify_admin_of_done(user_id, comment=None):
    mark_done(user_id, comment)
    clear_message_ts(user_id)
    try:
        profile = client.users_info(user=user_id)
        display_name = profile['user']['profile'].get('display_name') or profile['user']['real_name']
    except:
        display_name = user_id

    saved_comment = comment or get_comment(user_id) or ""
    message = f"✅ *{display_name}* marked their receipt upload as _Done_."
    if saved_comment.strip():
        message += f"\n📝 Comment: {saved_comment.strip()}"

    send_message(ADMIN_USER_ID, message)
    send_message(user_id, "✅ Thank you! Your receipt status has been marked as *Done*.")

def generate_status_overview():
    users = load_users()
    lines = []
    for u in users:
        uid = u['id']
        status = "✅ Done" if is_done(uid) else "🔴 Pending"
        comment = get_comment(uid) or ""
        line = f"• {u['name']} ({uid}) – {status}"
        if comment.strip():
            line += f"\n   📝 {comment.strip()}"
        lines.append(line)
    return "📊 *Status Overview:*\n" + "\n".join(lines)

def handle_status_command(user_id):
    overview = generate_status_overview()
    send_message(user_id, overview)
