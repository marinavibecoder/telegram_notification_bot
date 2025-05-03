#!/usr/bin/env python3
import asyncio
from telegram import Bot
import logging
import sys
import os
from datetime import datetime

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
            message = f"Scheduled notification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
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
    result = await send_notification("Scheduled notification from PythonAnywhere")
    
    if result:
        logger.info("Notification task completed successfully")
    else:
        logger.error("Notification task failed")

if __name__ == "__main__":
    asyncio.run(main()) 