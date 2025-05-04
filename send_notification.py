#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
import asyncio
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
            # Default config
            config = {
                "frequency_minutes": 60,
                "last_updated": datetime.now().isoformat()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"frequency_minutes": 60, "last_updated": datetime.now().isoformat()}

async def send_notification():
    """Send a notification message to the specified chat."""
    try:
        if not TOKEN:
            logger.error("Please set your bot token in the environment variables!")
            return
            
        # Load config to log current frequency
        config = load_config()
        logger.info(f"Current notification frequency: {config['frequency_minutes']} minutes")
            
        # User's custom message
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Hi Marina, you are a nice vibe coder don't forget it haha\n\n" \
                 f"Time: {current_time}"
        
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

if __name__ == "__main__":
    asyncio.run(send_notification()) 