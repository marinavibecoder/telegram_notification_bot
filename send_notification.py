#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
import asyncio
import sys
from telegram import Bot
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
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '105453726')

# Config file path
CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from config file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default config with basic schedule
            config = {
                "schedules": {
                    "basic": {
                        "frequency_minutes": 60,
                        "last_updated": datetime.now().isoformat(),
                        "message": "Hi Marina, you are a nice vibe coder don't forget it haha"
                    }
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            "schedules": {
                "basic": {
                    "frequency_minutes": 60,
                    "last_updated": datetime.now().isoformat(),
                    "message": "Hi Marina, you are a nice vibe coder don't forget it haha"
                }
            },
            "last_updated": datetime.now().isoformat()
        }

async def send_notification(schedule_name=None):
    """Send a notification message to the specified chat."""
    try:
        if not TOKEN:
            logger.error("Please set your bot token in the environment variables!")
            return
            
        # Load config
        config = load_config()
        
        # Determine which schedule to use
        if schedule_name is None:
            # If no schedule provided and 'basic' exists, use it
            if "basic" in config["schedules"]:
                schedule_name = "basic"
            # Otherwise use the first schedule in the config
            elif config["schedules"]:
                schedule_name = next(iter(config["schedules"]))
            else:
                logger.error("No schedules found in config!")
                return
        
        # Check if requested schedule exists
        if schedule_name not in config["schedules"]:
            logger.error(f"Schedule '{schedule_name}' not found in config!")
            return
            
        # Get schedule info
        schedule = config["schedules"][schedule_name]
        logger.info(f"Processing schedule '{schedule_name}' (every {schedule['frequency_minutes']} minutes)")
            
        # Get schedule-specific message
        message = schedule["message"]
        
        # Add time to message
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"{message}\n\nTime: {current_time}\n(From schedule: {schedule_name})"
        
        # Send the message
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=full_message)
        logger.info(f"Notification from schedule '{schedule_name}' sent successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

async def main():
    """Main function that processes command line arguments."""
    # Check for schedule name in command line arguments
    schedule_name = None
    if len(sys.argv) > 1:
        schedule_name = sys.argv[1]
        
    result = await send_notification(schedule_name)
    
    if result:
        logger.info("Notification task completed successfully")
    else:
        logger.error("Notification task failed")

if __name__ == "__main__":
    asyncio.run(main()) 