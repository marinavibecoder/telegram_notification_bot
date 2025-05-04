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
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        # Return default config if there's an error
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
    schedules_text = ""
    
    for name, schedule in config["schedules"].items():
        schedules_text += f"• {name}: every {schedule['frequency_minutes']} minutes\n"
    
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm your notification bot.\n\n"
        f"Your current schedules:\n{schedules_text}\n"
        f"Available commands:\n"
        f"/start - Show this help message\n"
        f"/change [schedule_name] [minutes] - Update frequency of a schedule\n"
        f"/create [schedule_name] [minutes] - Create a new schedule\n"
        f"/list - List all schedules\n"
        f"/send [schedule_name] - Send a test notification from a schedule"
    )

async def change_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change the frequency of an existing schedule."""
    global config
    
    try:
        # Check args: /change schedule_name minutes
        if len(context.args) != 2 or not context.args[1].isdigit():
            await update.message.reply_text(
                "Please provide a schedule name and a valid number of minutes.\n"
                "Example: /change basic 30"
            )
            return
            
        schedule_name = context.args[0].lower()
        minutes = int(context.args[1])
        
        if minutes < 1:
            await update.message.reply_text("Minutes must be at least 1.")
            return
            
        # Check if schedule exists
        if schedule_name not in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' not found. Available schedules:\n" +
                "\n".join([f"• {name}" for name in config["schedules"].keys()])
            )
            return
            
        # Update config
        config["schedules"][schedule_name]["frequency_minutes"] = minutes
        config["schedules"][schedule_name]["last_updated"] = datetime.now().isoformat()
        config["last_updated"] = datetime.now().isoformat()
        save_config(config)
        
        await update.message.reply_text(
            f"Schedule '{schedule_name}' updated to every {minutes} minutes.\n"
            f"Next notification will arrive in {minutes} minutes."
        )
        
        # Also send a notification to the original chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"Schedule '{schedule_name}' frequency changed to every {minutes} minutes."
        )
        
        logger.info(f"Schedule '{schedule_name}' frequency changed to {minutes} minutes")
        
    except Exception as e:
        logger.error(f"Error changing frequency: {e}")
        await update.message.reply_text(f"Error changing frequency: {e}")

async def create_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new schedule."""
    global config
    
    try:
        # Check args: /create schedule_name minutes
        if len(context.args) < 2 or not context.args[-1].isdigit():
            await update.message.reply_text(
                "Please provide a schedule name and a valid number of minutes.\n"
                "Example: /create pushups 30"
            )
            return
            
        # Get the name (can be multiple words) and minutes (last argument)
        minutes = int(context.args[-1])
        schedule_name = " ".join(context.args[:-1]).lower()
        
        if minutes < 1:
            await update.message.reply_text("Minutes must be at least 1.")
            return
            
        # Check if schedule already exists
        if schedule_name in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' already exists. Use /change to modify it."
            )
            return
            
        # Create custom message for this schedule
        custom_message = f"Hi Marina, don't forget your {schedule_name}!"
            
        # Create new schedule
        config["schedules"][schedule_name] = {
            "frequency_minutes": minutes,
            "last_updated": datetime.now().isoformat(),
            "message": custom_message
        }
        config["last_updated"] = datetime.now().isoformat()
        save_config(config)
        
        await update.message.reply_text(
            f"New schedule '{schedule_name}' created with {minutes} minute frequency.\n"
            f"Message: \"{custom_message}\""
        )
        
        # Also send a notification to the original chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"New schedule '{schedule_name}' created! It will remind you every {minutes} minutes."
        )
        
        logger.info(f"New schedule '{schedule_name}' created with {minutes} minute frequency")
        
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        await update.message.reply_text(f"Error creating schedule: {e}")

async def list_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all schedules."""
    try:
        if not config["schedules"]:
            await update.message.reply_text("No schedules found.")
            return
            
        schedules_text = "Your schedules:\n\n"
        
        for name, schedule in config["schedules"].items():
            schedules_text += f"• {name}\n"
            schedules_text += f"  Frequency: every {schedule['frequency_minutes']} minutes\n"
            schedules_text += f"  Message: \"{schedule['message']}\"\n\n"
        
        await update.message.reply_text(schedules_text)
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        await update.message.reply_text(f"Error listing schedules: {e}")

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test message from a specific schedule."""
    try:
        if not context.args:
            # Default to basic schedule if none specified
            schedule_name = "basic"
        else:
            schedule_name = " ".join(context.args).lower()
            
        if schedule_name not in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' not found. Available schedules:\n" +
                "\n".join([f"• {name}" for name in config["schedules"].keys()])
            )
            return
            
        # Get schedule-specific message
        schedule = config["schedules"][schedule_name]
        message = schedule["message"]
        
        # Add time to message
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"{message}\n\nTime: {current_time}\n(From schedule: {schedule_name})"
              
        await context.bot.send_message(chat_id=CHAT_ID, text=full_message)
        await update.message.reply_text(f"Test message sent from schedule '{schedule_name}'!")
        logger.info(f"Test message sent from schedule '{schedule_name}'")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text(f"Error sending message: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    await update.message.reply_text(
        "I understand these commands:\n"
        "/start - Show help information\n"
        "/change [schedule_name] [minutes] - Update frequency of a schedule\n"
        "/create [schedule_name] [minutes] - Create a new schedule\n"
        "/list - List all schedules\n"
        "/send [schedule_name] - Send a test notification from a schedule"
    )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change", change_frequency))
    application.add_handler(CommandHandler("create", create_schedule))
    application.add_handler(CommandHandler("list", list_schedules))
    application.add_handler(CommandHandler("send", send_message))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 