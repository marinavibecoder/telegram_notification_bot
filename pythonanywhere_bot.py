#!/usr/bin/env python3
import asyncio
from telegram import Bot
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
            # Get current time and day of week
            now = datetime.now()
            current_time = now.strftime('%Y-%m-%d %H:%M:%S')
            day_of_week = now.strftime('%A')
            
            # Customize message based on time of day
            hour = now.hour
            
            if hour < 12:
                greeting = "Good morning! ☀️"
                message_type = "Start your day with positivity!"
            elif hour < 17:
                greeting = "Good afternoon! 🌤️"
                message_type = "Keep going strong!"
            else:
                greeting = "Good evening! 🌙"
                message_type = "Wind down and relax."
                
            # Create a personalized message
            message = f"{greeting}\n\n" \
                      f"📅 {day_of_week}, {current_time}\n" \
                      f"📝 {message_type}\n\n" \
                      f"This is your scheduled reminder from PythonAnywhere."
            
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

async def main():
    """Main function to send a notification."""
    if TOKEN == 'YOUR_BOT_TOKEN' or CHAT_ID == 'YOUR_CHAT_ID':
        logger.error("Please set your bot token and chat ID in the script!")
        sys.exit(1)
        
    logger.info("Running scheduled notification task")
    
    # Send notification
    result = await send_notification()  # Using the default, time-based message
    
    if result:
        logger.info("Notification task completed successfully")
    else:
        logger.error("Notification task failed")

if __name__ == "__main__":
    asyncio.run(main()) 