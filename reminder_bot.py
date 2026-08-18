import os
import time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_recent_logs

# Pulls the Telegram bot token and chat ID from environment variables from Render.com
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

def send_telegram_reminder():
    # Check if there are any logs for today
    today_logs = get_recent_logs(days=1)
    
    if not today_logs:
        message = "Hey! Haven't heard from you today. Did you manage to get any rest or a run in? Drop by the app to log it!"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        try:
            requests.get(url)
            print("Reminder sent successfully!")
        except Exception as e:
            print(f"Failed to send reminder: {e}")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # Schedule the job to run every day at 8:00 PM (20:00)
    scheduler.add_job(send_telegram_reminder, 'cron', hour=20, minute=0)
    scheduler.start()
    
    print("Reminder bot started and running in background...")
    
    # Keep the script alive
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()