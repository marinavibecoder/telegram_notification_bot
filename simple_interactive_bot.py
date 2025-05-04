#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
import time

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
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
    global config
    
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
        
        await update.message.reply_text(
            f"Notification frequency updated to every {minutes} minutes.\n"
            f"Next notification will arrive in {minutes} minutes."
        )
        
        # Also send a notification to the original chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"Notification frequency changed to every {minutes} minutes."
        )
        
        logger.info(f"Notification frequency changed to {minutes} minutes")
        
    except Exception as e:
        logger.error(f"Error changing frequency: {e}")
        await update.message.reply_text(f"Error changing frequency: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    await update.message.reply_text(
        "I understand these commands:\n"
        "/start - Get information about the bot\n"
        "/change [minutes] - Change notification frequency\n\n"
        f"Current notification frequency: Every {config['frequency_minutes']} minutes"
    )

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test message now."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"Hi Marina, you are a nice vibe coder don't forget it haha\n\n" \
              f"Time: {current_time}"
              
    await context.bot.send_message(chat_id=CHAT_ID, text=message)
    await update.message.reply_text("Test message sent!")
    logger.info("Test message sent")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change", change_frequency))
    application.add_handler(CommandHandler("send", send_message))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 