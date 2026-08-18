from datetime import datetime, timedelta
import pytz
import requests


def fetch_singapore_holidays():
  """Fetches official Singapore public holidays for the current year from Nager.Date API."""
  current_year = datetime.now().year
  url = f"https://date.nager.at/api/v3/PublicHolidays/{current_year}/SG"

  try:
    response = requests.get(url)
    if response.status_code == 200:
      return response.json()  # Returns a list of holiday dictionaries
  except Exception as e:
    print(f"Error fetching calendar API: {e}")

  return []


def check_upcoming_sg_events(days_ahead=3):
  """Checks if any public holiday or special event is coming up in the next few days."""
  SGT = pytz.timezone("Asia/Singapore")
  today = datetime.now(SGT)
  upcoming_alerts = []

  holidays = fetch_singapore_holidays()

  for i in range(days_ahead + 1):
    target_date = today + timedelta(days=i)
    target_date_str = target_date.strftime("%Y-%m-%d")

    # Check against fetched public holidays
    for holiday in holidays:
      if holiday.get("date") == target_date_str:
        holiday_name = holiday.get("localName")
        if i == 0:
          upcoming_alerts.append(
              f"🎉 Today is **{holiday_name}** in Singapore! Take a moment to"
              " celebrate or take a break."
          )
        else:
          upcoming_alerts.append(
              f"⏰ Reminder: **{holiday_name}** is coming up in {i} day(s)!"
          )

    # Hardcode cultural/custom milestones like Valentine's Day since APIs usually only track public holidays
    if target_date.strftime("%m-%d") == "02-14":
      if i == 0:
        upcoming_alerts.append(
            "❤️ Today is **Valentine's Day**! Don't forget to take a break and"
            " spend time with your loved ones."
        )
      else:
        upcoming_alerts.append(
            f"⏰ Reminder: **Valentine's Day** is coming up in {i} day(s)!"
        )

  return upcoming_alerts