# tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from store import load_users, is_done, reset_status, get_comment
from slack import send_message
from slack_sdk import WebClient
import os

client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

scheduler = BackgroundScheduler()

ADMIN_USER_ID = os.environ.get("SLACK_ADMIN_USER_ID")

def daily_check(force=False):
    today = datetime.today().day
    log = []

    if not force:
        if today == 10:
            reset_status()
            if ADMIN_USER_ID:
                send_message(ADMIN_USER_ID, "🔄 Monthly receipt statuses have been reset.")
            return

        if today > 4:
            return

    users = load_users()
    for user in users:
        user_id = user['id']
        if is_done(user_id):
            comment = get_comment(user_id) or "No comment."
            done_msg = f"✅ You already marked this month as *Done*.\n📝 *Comment:* {comment}"
            send_message(user_id, done_msg)
            continue

        text = "📌 *Monthly Receipt Reminder*\nPlease upload your receipts and click below when done."
        if not force and today == 4:
            text = "⚠️ *Final Reminder*\nPlease upload your receipts *today*. This is the last call."

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            },
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
        ]

        send_message(user_id, text, blocks=blocks)

        log_entry = f"{'⚠️ Final notice' if not force and today == 4 else '🔁 Reminder'} sent to <@{user_id}>"
        log.append(log_entry)

    if log and ADMIN_USER_ID:
        report = f"📅 *Reminder Log – {datetime.today().strftime('%Y-%m-%d')}*\n" + "\n".join(log)
        send_message(ADMIN_USER_ID, report)

def send_summary_to_admin():
    users = load_users()
    summary = []
    for u in users:
        status = is_done(u['id'])
        comment = get_comment(u['id'])
        summary.append(f"• {u['name']} – {'✅ Done' if status else '❌ Pending'}" + (f"\n   📝 {comment}" if status and comment else ""))
    message = "📊 *Monthly Upload Status Summary:*\n" + "\n".join(summary)
    send_message(ADMIN_USER_ID, message)

def start_scheduler():
    scheduler.add_job(daily_check, 'cron', hour=9)
    scheduler.add_job(send_summary_to_admin, CronTrigger(day=3, hour=12, timezone='CET'))
    scheduler.add_job(send_summary_to_admin, CronTrigger(day=4, hour=12, timezone='CET'))
    scheduler.start()
