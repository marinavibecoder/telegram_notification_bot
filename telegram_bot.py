#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import logging
from datetime import datetime
import re

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"frequency_minutes": 60, "last_updated": datetime.now().isoformat()}

def save_config(config):
    """Save configuration to config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

# Load initial config
config = load_config()
scheduler = None

async def send_notification(context=None):
    """Send a notification message to the specified chat."""
    try:
        # User's custom message
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Hi Marina, you are a nice vibe coder don't forget it haha\n\n" \
                 f"Time: {current_time}"
        
        if context:
            # Called from the scheduler
            await context.bot.send_message(chat_id=CHAT_ID, text=message)
        else:
            # Called directly
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=message)
            
        logger.info(f"Notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm your notification bot.\n\n"
        f"I'll send you messages saying 'Hi Marina, you are a nice vibe coder don't forget it haha'\n\n"
        f"Current notification frequency: Every {config['frequency_minutes']} minutes\n\n"
        f"Use /change [minutes] to update the frequency."
    )

async def change_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change the notification frequency."""
    global config, scheduler
    
    try:
        # Get the minutes from command
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "Please provide a valid number of minutes.\n"
                "Example: /change 30"
            )
            return
            
        minutes = int(context.args[0])
        
        if minutes < 1:
            await update.message.reply_text("Minutes must be at least 1.")
            return
            
        # Update config
        config["frequency_minutes"] = minutes
        config["last_updated"] = datetime.now().isoformat()
        save_config(config)
        
        # Update scheduler
        # Remove existing job
        for job in scheduler.get_jobs():
            if job.id == 'notification_job':
                job.remove()
                
        # Add new job with updated frequency
        scheduler.add_job(
            lambda: asyncio.create_task(send_notification(context)), 
            'interval', 
            minutes=minutes,
            id='notification_job'
        )
        
        await update.message.reply_text(
            f"Notification frequency updated to every {minutes} minutes.\n"
            f"Next notification will arrive in {minutes} minutes."
        )
        
        logger.info(f"Notification frequency changed to {minutes} minutes")
        
    except Exception as e:
        logger.error(f"Error changing frequency: {e}")
        await update.message.reply_text(f"Error changing frequency: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    # Check if it's a frequency change request in plain text (not command)
    message_text = update.message.text
    
    # Look for pattern like "change 30" or "change to 30 minutes"
    match = re.search(r'change\s+(?:to\s+)?(\d+)(?:\s+minutes?)?', message_text, re.IGNORECASE)
    
    if match:
        # Extract the minutes
        minutes = int(match.group(1))
        # Create a context args array similar to what the command handler expects
        context.args = [str(minutes)]
        # Call the change frequency function
        await change_frequency(update, context)
    else:
        await update.message.reply_text(
            "I understand these commands:\n"
            "/start - Get information about the bot\n"
            "/change [minutes] - Change notification frequency\n\n"
            f"Current notification frequency: Every {config['frequency_minutes']} minutes"
        )

async def main():
    """Start the bot."""
    global scheduler
    
    # Validate token
    if not TOKEN:
        logger.error("Please set your bot token in the environment variables!")
        sys.exit(1)
        
    logger.info("Starting the notification bot")
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change", change_frequency))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()
    
    # Schedule notification job with current frequency
    scheduler.add_job(
        lambda: asyncio.create_task(send_notification(application)), 
        'interval', 
        minutes=config['frequency_minutes'],
        id='notification_job'
    )
    
    # Send initial notification
    await send_notification(application)
    
    logger.info(f"Bot started with notification frequency: {config['frequency_minutes']} minutes")
    
    # Run the bot until the user presses Ctrl-C
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())