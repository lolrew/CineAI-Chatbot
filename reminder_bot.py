import os
import time
import requests
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_recent_logs

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
USER_TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")

def send_telegram_reminder():
    # get_recent_logs(days=1) checks if there's any activity/logs for today
    today_logs = get_recent_logs(days=1)
    
    # If no logs/chat activity happened today, send the Telegram nudge
    if not today_logs:
        message = "Hey! Haven't heard from you or seen any logs today. Did you manage to get any rest or a run in? Drop by the app to update!"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        try:
            requests.post(url, json=payload)
            print("Habit reminder sent successfully because no activity was found today!")
        except Exception as e:
            print(f"Failed to send reminder: {e}")
    else:
        print("Activity found for today. Skipping Telegram reminder.")

if __name__ == "__main__":
    tz = pytz.timezone(USER_TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)
    
    # Runs the check every day at 8:00 PM
    scheduler.add_job(send_telegram_reminder, 'cron', hour=20, minute=0)
    scheduler.start()
    
    print("Activity-based reminder bot started and running...")
    
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()