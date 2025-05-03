# Telegram Notification Bot

A simple Telegram bot that sends scheduled notifications.

## Setup

1. Install the dependencies:
   ```
   pip3 install -r requirements.txt
   ```

2. Get your Chat ID:
   - Run the test bot to get instructions:
     ```
     python3 test_bot.py
     ```
   - Follow the instructions to get your chat ID
   - Open `telegram_bot.py` and update the `CHAT_ID` variable with your chat ID

3. Start the bot:
   ```
   python3 telegram_bot.py
   ```

## Customizing Notifications

Edit the `telegram_bot.py` file to change the notification schedule:

- For interval-based notifications, modify:
  ```python
  scheduler.add_job(send_notification, 'interval', hours=1)
  ```

- For scheduled notifications at specific times, uncomment and modify:
  ```python
  scheduler.add_job(lambda: asyncio.create_task(send_notification("Daily reminder!")), 'cron', hour=9, minute=0)
  ```

## APScheduler Options

- **Interval**: Run jobs at fixed intervals (seconds, minutes, hours, days, weeks)
- **Cron**: Run jobs at specific times, similar to Unix cron
- **Date**: Run jobs once at a specific date and time

For more information on scheduling options, visit the [APScheduler documentation](https://apscheduler.readthedocs.io/en/stable/userguide.html). 