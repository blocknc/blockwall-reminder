# tasks.py
from store import load_users, is_done, reset_status
from slack import send_message
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

scheduler = BackgroundScheduler()

def daily_check(force=False):
    today = datetime.now().day
    users = load_users()

    if not users:
        print("📭 Keine Reminder-User eingetragen.")
        return

    for u in users:
        uid = u['id']
        name = u['name']

        if today in [1, 2, 3] or force:
            if is_done(uid):
                continue  # skip sending if already done
            send_message(uid, text="Reminder", blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📌 *Monthly Receipt Reminder*
Please upload your receipts and click below when done."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark as Done"},
                            "action_id": "open_reminder_modal"
                        }
                    ]
                }
            ])

        elif today == 4:
            if not is_done(uid):
                send_message(uid, "⚠️ *Last Reminder!*\nPlease upload your receipts today.")

        elif today == 10:
            reset_status()
            send_message(uid, "🔁 *Reminder cycle reset for the new month.*")

    if force:
        send_message(os.environ.get("SLACK_ADMIN_USER_ID"), f"📅 Reminder Log – {datetime.today().strftime('%Y-%m-%d')}\n:repeat: Reminder sent to \n" + "\n".join([f"<@{u['id']}>" for u in users if not is_done(u['id'])]))

def start_scheduler():
    scheduler.add_job(daily_check, 'cron', hour=9, timezone=timezone('Europe/Berlin'))
    scheduler.start()
