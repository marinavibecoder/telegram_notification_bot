#!/usr/bin/env python3
import asyncio
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = os.environ.get('TELEGRAM_TOKEN')  # Get token from environment variable
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '105453726')  # Your chat ID

async def send_notification(message=None):
    """Send a notification message to the specified chat."""
    try:
        if message is None:
            # Customize your default notification message here
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"🔔 Your hourly reminder! Time: {current_time}\n\n" \
                     f"Hope you're having a productive day! 💪"
            
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

async def main():
    """Main function to set up and start the scheduler."""
    if TOKEN == 'YOUR_BOT_TOKEN' or CHAT_ID == 'YOUR_CHAT_ID':
        logger.error("Please set your bot token and chat ID in the script!")
        sys.exit(1)
        
    logger.info("Starting the notification bot")
    
    # Create a scheduler
    scheduler = AsyncIOScheduler()
    
    # Schedule the notification to run every hour
    scheduler.add_job(send_notification, 'interval', hours=1)
    
    # You can add more scheduled notifications with different intervals and messages
    # scheduler.add_job(lambda: asyncio.create_task(send_notification("⏰ Time for your daily task check!")), 'cron', hour=9, minute=0)
    # scheduler.add_job(lambda: asyncio.create_task(send_notification("🍽️ Don't forget lunch break!")), 'cron', hour=12, minute=0)
    # scheduler.add_job(lambda: asyncio.create_task(send_notification("🧘 Time for a short meditation break")), 'cron', hour=15, minute=0)
    # scheduler.add_job(lambda: asyncio.create_task(send_notification("📝 Remember to wrap up your daily tasks")), 'cron', hour=17, minute=0)
    
    try:
        # Send an initial notification
        await send_notification("🚀 Bot started! You will receive notifications based on the schedule.")
        
        # Start the scheduler
        scheduler.start()
        
        # Keep the program running
        while True:
            await asyncio.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())