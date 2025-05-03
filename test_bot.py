#!/usr/bin/env python3
import asyncio
from telegram import Bot
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = '7576461921:AAE6M8r5bI-6tuc8k9rUaaNzzfDlgqskxa8'

# Main function
async def main():
    logger.info("Testing bot notification")
    
    try:
        bot = Bot(token=TOKEN)
        # Get me information (to get your chat ID)
        me = await bot.get_me()
        logger.info(f"Bot info: {me.to_dict()}")
        logger.info("To get your chat ID, start a conversation with your bot and use @userinfobot")
        
        # Uncomment and replace with your chat ID when you have it
        # CHAT_ID = "YOUR_CHAT_ID_HERE"
        # await bot.send_message(chat_id=CHAT_ID, text=f"Test message sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # logger.info(f"Test message sent to {CHAT_ID}")
        
        logger.info("Instructions to get your chat ID:")
        logger.info("1. Start a conversation with your bot on Telegram")
        logger.info("2. Send a message to your bot")
        logger.info("3. Visit https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        logger.info(f"   Replace <YOUR_TOKEN> with your actual token")
        logger.info(f"   Full URL: https://api.telegram.org/bot{TOKEN}/getUpdates")
        logger.info("4. Look for 'chat':{'id': YOUR_CHAT_ID} in the response")
        logger.info("5. Copy that ID and use it in your telegram_bot.py file")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
