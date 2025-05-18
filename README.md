# Telegram Notification Bot

A Telegram bot that sends scheduled notifications with support for multiple independent schedules.

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
   - Create a `.env` file with your credentials:
     ```
     TELEGRAM_TOKEN=your_bot_token_here
     TELEGRAM_CHAT_ID=your_chat_id_here
     ```

3. Start the bot:
   ```
   python3 simple_interactive_bot.py
   ```

## Available Commands

The bot supports the following commands:

- `/start` - Show help information and current schedules
- `/change [schedule_name] [minutes]` - Update frequency of a schedule
- `/create [schedule_name] [minutes]` - Create a new schedule
- `/delete [schedule_name]` - Delete a schedule
- `/list` - List all schedules with their messages
- `/all` - Show detailed timing information for all schedules
- `/timer [schedule_name]` - Show time until next notification
- `/refresh [schedule_name]` - Reset timer to start from now
- `/send [schedule_name]` - Send a test notification from a schedule

## Schedule Management

Each schedule can have:
- A custom name
- Its own frequency (in minutes)
- A custom notification message
- Independent timing

The bot will automatically manage multiple schedules and send notifications according to each schedule's frequency.

## Configuration

Schedules are stored in `config.json`. The bot will create this file automatically with a default schedule if it doesn't exist.

For more information on scheduling options, visit the [APScheduler documentation](https://apscheduler.readthedocs.io/en/stable/userguide.html). 