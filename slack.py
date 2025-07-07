# slack.py
import o
from slack_sdk import WebClient
from store import is_done, get_comment

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
                    "📥 *Receipt Reminder*\nPlease upload your receipts for last month.\nClick *Done* once you've completed the upload."
                )
            }
        },
        {
            "type": "input",
            "block_id": "upload_comment",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": "Optional comment (e.g. missing receipts)"
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

def notify_admin_of_done(user_id, comment=None):
    if not is_done(user_id):
        return  # prevent double-message
    try:
        profile = client.users_info(user=user_id)
        display_name = profile['user']['profile'].get('display_name') or profile['user']['real_name']
    except:
        display_name = user_id

    message = f"✅ *{display_name}* marked their receipt upload as _Done_."
    saved_comment = comment or get_comment(user_id)
    if saved_comment:
        message += f"\n📝 Comment: {saved_comment}"
    send_message(ADMIN_USER_ID, message)
    send_message(user_id, "✅ Thank you! Your receipt status has been marked as *Done*.")
