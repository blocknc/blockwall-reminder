# tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from store import load_users, is_done, save_users, mark_done, reset_status
from slack import send_message, send_modal
from slack_sdk import WebClient
import os

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

scheduler = BackgroundScheduler()

ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

def daily_check():
    today = datetime.today().day
    log = []

    if today == 10:
        reset_status()
        if ADMIN_USER_ID:
            send_message(ADMIN_USER_ID, "🔄 Monthly receipt statuses have been reset.")
        return

    if today > 4:
        return

    users = load_users()
    for user_id in users:
        if is_done(user_id):
            continue

        if today in [1, 2, 3]:
            send_message(user_id, "📌 *Monthly Receipt Reminder*
Please upload your receipts and click below when done.", blocks=[
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark as Done"},
                            "action_id": "open_reminder_modal",
                            "value": user_id
                        }
                    ]
                }
            ])
            log.append(f"🔁 Reminder sent to <@{user_id}> (Day {today})")
        elif today == 4:
            send_message(user_id, "⚠️ Final notice: Upload your receipts today or you'll miss the deadline!", blocks=[
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark as Done"},
                            "action_id": "open_reminder_modal",
                            "value": user_id
                        }
                    ]
                }
            ])
            log.append(f"⚠️ Final notice sent to <@{user_id}>")

    if log and ADMIN_USER_ID:
        report = f"📅 *Reminder Log – {datetime.today().strftime('%Y-%m-%d')}*
" + "
".join(log)
        send_message(ADMIN_USER_ID, report)

def start_scheduler():
    scheduler.add_job(daily_check, 'cron', hour=9)
    scheduler.start()
