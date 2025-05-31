#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime, timedelta
import time
import threading
import sys
import signal
import psutil
import subprocess

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to check for running instances and handle them
def check_for_running_instances():
    """Check if there's already a running instance of this bot and handle it."""
    # First check if we have a PID file
    pid_file = "bot_pid.txt"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process with this PID exists
            if psutil.pid_exists(old_pid):
                process = psutil.Process(old_pid)
                # Check if it's a Python process
                if "python" in process.name().lower():
                    logger.info(f"Found running bot instance with PID {old_pid}. Stopping it.")
                    # Send SIGTERM to gracefully stop the process
                    os.kill(old_pid, signal.SIGTERM)
                    # Wait for it to stop
                    time.sleep(2)
        except Exception as e:
            logger.warning(f"Error checking for existing bot instance: {e}")
    
    # Write current PID to file
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"Started new bot instance with PID {os.getpid()}")

# Bot Configuration
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '105453726')

# Config file path
CONFIG_FILE = 'config.json'

# Global variables for application and scheduler
application = None
stop_threads = False  # Flag to control the scheduler thread
BOT_STATE_FILE = 'bot_state.json'

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

def load_bot_state():
    """Load bot state from file."""
    try:
        if os.path.exists(BOT_STATE_FILE):
            with open(BOT_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default state is stopped
            state = {"is_running": False}
            save_bot_state(state)
            return state
    except Exception as e:
        logger.error(f"Error loading bot state: {e}")
        return {"is_running": False}

def save_bot_state(state):
    """Save bot state to file."""
    try:
        with open(BOT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving bot state: {e}")

# Load initial config
config = load_config()

# Load initial bot state
bot_state = load_bot_state()

def get_time_slot(dt):
    """Get the 10-minute time slot for a given datetime.
    Returns a tuple of (slot_start, slot_end) where both are datetime objects.
    Slots start at XX:00, XX:10, XX:20, etc."""
    # Round down to the nearest 10 minutes
    minutes = (dt.minute // 10) * 10
    slot_start = dt.replace(minute=minutes, second=1, microsecond=0)
    slot_end = slot_start + timedelta(minutes=10)
    return slot_start, slot_end

def get_next_slot_start():
    """Get the start time of the next 10-minute slot."""
    now = datetime.now()
    slot_start, _ = get_time_slot(now)
    if now >= slot_start:
        slot_start += timedelta(minutes=10)
    return slot_start

def scheduler_thread():
    """Thread function to check and send scheduled notifications."""
    logger.info("Scheduler thread started")
    last_slot_start = None
    
    while not stop_threads:
        try:
            # Only process notifications if bot is running
            if not bot_state["is_running"]:
                time.sleep(1)  # Sleep briefly when bot is stopped
                continue
                
            now = datetime.now()
            current_slot_start, current_slot_end = get_time_slot(now)
            
            # Only process at the start of a new slot (first second)
            if last_slot_start != current_slot_start and now.second < 2:
                logger.info(f"Processing slot starting at {current_slot_start.strftime('%H:%M:%S')}")
                last_slot_start = current_slot_start
                
                # Collect all schedules that need notification in this slot
                slot_notifications = []
                
                for name, schedule in config["schedules"].items():
                    try:
                        frequency_minutes = schedule["frequency_minutes"]
                        last_updated = datetime.fromisoformat(schedule["last_updated"])
                        
                        # Calculate when the next notification should be
                        next_notification = last_updated + timedelta(minutes=frequency_minutes)
                        
                        # If the next notification falls within the current 10-minute slot
                        if current_slot_start <= next_notification < current_slot_end:
                            logger.info(f"Schedule '{name}' needs notification in slot {current_slot_start.strftime('%H:%M')}-{current_slot_end.strftime('%H:%M')}")
                            slot_notifications.append({
                                "name": name,
                                "message": schedule["message"],
                                "frequency": frequency_minutes,
                                "next_time": next_notification
                            })
                            
                            # Update the last_updated timestamp
                            config["schedules"][name]["last_updated"] = now.isoformat()
                            config["last_updated"] = now.isoformat()
                            
                    except Exception as e:
                        logger.error(f"Error processing schedule '{name}': {e}")
                
                # If we have any notifications for this slot, send them as one consolidated message
                if slot_notifications:
                    try:
                        # Sort notifications by their scheduled time
                        slot_notifications.sort(key=lambda x: x["next_time"])
                        
                        # Create consolidated message
                        slot_time = current_slot_start.strftime('%H:%M')
                        consolidated_message = f"📅 Notifications for {slot_time}-{(current_slot_start + timedelta(minutes=10)).strftime('%H:%M')}\n\n"
                        
                        for notification in slot_notifications:
                            scheduled_time = notification["next_time"].strftime('%H:%M:%S')
                            consolidated_message += f"• {notification['message']}\n"
                            consolidated_message += f"  (From schedule: {notification['name']}, every {notification['frequency']} minutes, scheduled for {scheduled_time})\n\n"
                        
                        # Send the consolidated message
                        success = send_telegram_message(consolidated_message)
                        
                        if success:
                            save_config(config)
                            logger.info(f"Consolidated notification sent for {len(slot_notifications)} schedules in slot {slot_time}")
                        else:
                            logger.error("Failed to send consolidated notification")
                            
                    except Exception as e:
                        logger.error(f"Error sending consolidated notification: {e}")
            
            # Sleep until next second
            next_second = now.replace(microsecond=0) + timedelta(seconds=1)
            sleep_seconds = (next_second - now).total_seconds()
            time.sleep(max(0.1, sleep_seconds))  # Sleep at least 0.1 seconds
                
        except Exception as e:
            logger.error(f"Error in scheduler thread: {e}")
            time.sleep(5)  # Sleep briefly on error to prevent tight loop

def send_telegram_message(message):
    """Send a message to Telegram using HTTP API directly."""
    import requests
    
    try:
        logger.info(f"Sending Telegram message: {message[:50]}...")
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message
        }
        
        response = requests.post(url, data=data, timeout=10)  # Add timeout
        if response.status_code == 200:
            logger.info("Telegram message sent successfully!")
            return True
        else:
            logger.error(f"Failed to send message: Status {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

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
        f"/delete [schedule_name] - Delete a schedule\n"
        f"/list - List all schedules\n"
        f"/all - Show detailed timing for all schedules\n"
        f"/timer [schedule_name] - Show time until next notification\n"
        f"/refresh [schedule_name] - Reset timer to start from now\n"
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

async def delete_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete an existing schedule."""
    global config
    
    try:
        # Check args: /delete schedule_name
        if not context.args:
            await update.message.reply_text(
                "Please provide a schedule name to delete.\n"
                "Example: /delete dance"
            )
            return
            
        # Get the name (can be multiple words)
        schedule_name = " ".join(context.args).lower()
            
        # Check if schedule exists
        if schedule_name not in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' not found. Available schedules:\n" +
                "\n".join([f"• {name}" for name in config["schedules"].keys()])
            )
            return
            
        # Don't allow deleting the last schedule
        if len(config["schedules"]) <= 1:
            await update.message.reply_text(
                f"Cannot delete the last remaining schedule '{schedule_name}'.\n"
                f"Create a new schedule first before deleting this one."
            )
            return
            
        # Delete the schedule
        deleted_schedule = config["schedules"].pop(schedule_name)
        config["last_updated"] = datetime.now().isoformat()
        save_config(config)
        
        await update.message.reply_text(
            f"Schedule '{schedule_name}' has been deleted."
        )
        
        # Also send a notification to the original chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"Schedule '{schedule_name}' has been deleted from your notifications."
        )
        
        logger.info(f"Schedule '{schedule_name}' has been deleted")
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        await update.message.reply_text(f"Error deleting schedule: {e}")

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

async def all_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed timing information for all schedules."""
    try:
        if not config["schedules"]:
            await update.message.reply_text("No schedules found.")
            return
            
        now = datetime.now()
        schedules_text = "📋 All schedule details:\n\n"
        
        for name, schedule in config["schedules"].items():
            # Calculate timing information
            frequency_minutes = schedule["frequency_minutes"]
            last_updated = datetime.fromisoformat(schedule["last_updated"])
            
            # Calculate next notification time
            minutes_since_update = (now - last_updated).total_seconds() / 60
            minutes_until_next = frequency_minutes - (minutes_since_update % frequency_minutes)
            next_notification = now + timedelta(minutes=minutes_until_next)
            
            # Calculate how many times it runs per day
            runs_per_day = 24 * 60 / frequency_minutes
            
            # Format the message
            schedules_text += f"🔔 *{name}*\n"
            schedules_text += f"  • Frequency: every *{frequency_minutes} minutes*\n"
            schedules_text += f"  • Next notification: *{next_notification.strftime('%H:%M:%S')}* "
            schedules_text += f"(in {int(minutes_until_next)} minutes)\n"
            schedules_text += f"  • Notifications per day: *{runs_per_day:.1f}*\n"
            schedules_text += f"  • Message: \"{schedule['message']}\"\n\n"
        
        await update.message.reply_text(schedules_text)
        
    except Exception as e:
        logger.error(f"Error showing all schedules: {e}")
        await update.message.reply_text(f"Error showing all schedules: {e}")

async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show time until next notification for a specific schedule."""
    try:
        # Check if schedule name is provided
        if not context.args:
            await update.message.reply_text(
                "Please provide a schedule name.\n"
                "Example: /timer basic"
            )
            return
            
        # Get the schedule name
        schedule_name = " ".join(context.args).lower()
        
        # Check if schedule exists
        if schedule_name not in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' not found. Available schedules:\n" +
                "\n".join([f"• {name}" for name in config["schedules"].keys()])
            )
            return
            
        # Get the schedule
        schedule = config["schedules"][schedule_name]
        frequency_minutes = schedule["frequency_minutes"]
        last_updated = datetime.fromisoformat(schedule["last_updated"])
        
        # Calculate next notification time
        now = datetime.now()
        minutes_since_update = (now - last_updated).total_seconds() / 60
        minutes_until_next = frequency_minutes - (minutes_since_update % frequency_minutes)
        next_notification = now + timedelta(minutes=minutes_until_next)
        
        # Format the message
        message = f"⏱️ Timer for '{schedule_name}':\n\n"
        message += f"• Next notification in: {int(minutes_until_next)} minutes\n"
        message += f"• Exact time: {next_notification.strftime('%H:%M:%S')}\n"
        message += f"• Message that will be sent: \"{schedule['message']}\""
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error showing timer: {e}")
        await update.message.reply_text(f"Error showing timer: {e}")

async def refresh_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset a schedule's timer to start from now."""
    global config
    
    try:
        # Check if schedule name is provided
        if not context.args:
            await update.message.reply_text(
                "Please provide a schedule name to refresh.\n"
                "Example: /refresh basic"
            )
            return
            
        # Get the schedule name
        schedule_name = " ".join(context.args).lower()
        
        # Check if schedule exists
        if schedule_name not in config["schedules"]:
            await update.message.reply_text(
                f"Schedule '{schedule_name}' not found. Available schedules:\n" +
                "\n".join([f"• {name}" for name in config["schedules"].keys()])
            )
            return
            
        # Update the last_updated timestamp to now
        now = datetime.now()
        config["schedules"][schedule_name]["last_updated"] = now.isoformat()
        config["last_updated"] = now.isoformat()
        save_config(config)
        
        await update.message.reply_text(
            f"🔄 Timer for '{schedule_name}' has been refreshed!\n\n"
            f"• Next notification will be in {config['schedules'][schedule_name]['frequency_minutes']} minutes\n"
            f"• Exact time: {now.strftime('%H:%M:%S')}"
        )
        
        # Also send a notification to the original chat ID
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"Schedule '{schedule_name}' timer has been refreshed. Next notification in {config['schedules'][schedule_name]['frequency_minutes']} minutes."
        )
        
        logger.info(f"Schedule '{schedule_name}' timer has been refreshed")
        
    except Exception as e:
        logger.error(f"Error refreshing timer: {e}")
        await update.message.reply_text(f"Error refreshing timer: {e}")

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
        "/delete [schedule_name] - Delete a schedule\n"
        "/list - List all schedules\n"
        "/all - Show detailed timing for all schedules\n"
        "/timer [schedule_name] - Show time until next notification\n"
        "/refresh [schedule_name] - Reset timer to start from now\n"
        "/send [schedule_name] - Send a test notification from a schedule\n"
        "/control [start|stop] - Start or stop the bot\n"
        "/status - Show current bot status"
    )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond to unknown commands."""
    command = update.message.text.split()[0]
    await update.message.reply_text(
        f"Sorry, I don't understand the command '{command}'.\n\n"
        "Here are the available commands:\n"
        "/start - Show help information and current schedules\n"
        "/change [schedule_name] [minutes] - Update frequency of a schedule\n"
        "/create [schedule_name] [minutes] - Create a new schedule\n"
        "/delete [schedule_name] - Delete a schedule\n"
        "/list - List all schedules with their messages\n"
        "/all - Show detailed timing information for all schedules\n"
        "/timer [schedule_name] - Show time until next notification\n"
        "/refresh [schedule_name] - Reset timer to start from now\n"
        "/send [schedule_name] - Send a test notification from a schedule\n"
        "/control [start|stop] - Start or stop the bot\n"
        "/status - Show current bot status"
    )

def signal_handler(sig, frame):
    """Handle signals (like SIGTERM, SIGINT) to ensure clean shutdown."""
    logger.info(f"Received signal {sig}, shutting down...")
    global stop_threads, application
    
    # Stop scheduler thread
    stop_threads = True
    
    # Stop application if it's running
    if application:
        application.stop()
    
    # Exit
    sys.exit(0)

async def control_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Control the bot's state (start/stop)."""
    global bot_state
    
    try:
        if not context.args:
            await update.message.reply_text(
                "Please specify an action: start or stop\n"
                "Example: /control start"
            )
            return
            
        action = context.args[0].lower()
        
        if action not in ['start', 'stop']:
            await update.message.reply_text(
                "Invalid action. Use 'start' or 'stop'.\n"
                "Example: /control start"
            )
            return
            
        if action == 'start' and bot_state["is_running"]:
            await update.message.reply_text("Bot is already running!")
            return
            
        if action == 'stop' and not bot_state["is_running"]:
            await update.message.reply_text("Bot is already stopped!")
            return
            
        if action == 'start':
            bot_state["is_running"] = True
            save_bot_state(bot_state)
            await update.message.reply_text("✅ Bot has been started! Notifications will resume.")
            logger.info("Bot started by user command")
            
        else:  # stop
            bot_state["is_running"] = False
            save_bot_state(bot_state)
            await update.message.reply_text("🛑 Bot has been stopped! No more notifications will be sent.")
            logger.info("Bot stopped by user command")
            
    except Exception as e:
        logger.error(f"Error controlling bot: {e}")
        await update.message.reply_text(f"Error controlling bot: {e}")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current status of the bot."""
    status = "running" if bot_state["is_running"] else "stopped"
    status_emoji = "✅" if bot_state["is_running"] else "🛑"
    
    message = f"Bot Status: {status_emoji} {status.upper()}\n\n"
    
    if bot_state["is_running"]:
        message += "Active schedules:\n"
        for name, schedule in config["schedules"].items():
            last_updated = datetime.fromisoformat(schedule["last_updated"])
            now = datetime.now()
            minutes_since_update = (now - last_updated).total_seconds() / 60
            minutes_until_next = schedule["frequency_minutes"] - (minutes_since_update % schedule["frequency_minutes"])
            next_notification = now + timedelta(minutes=minutes_until_next)
            
            message += f"• {name}: next notification in {int(minutes_until_next)} minutes ({next_notification.strftime('%H:%M:%S')})\n"
    else:
        message += "Bot is currently stopped. Use /control start to start it."
    
    await update.message.reply_text(message)

def reset_all_schedules():
    """Reset all schedule timestamps to current time."""
    global config
    now = datetime.now().isoformat()
    for schedule in config["schedules"].values():
        schedule["last_updated"] = now
    config["last_updated"] = now
    save_config(config)
    logger.info("All schedule timestamps have been reset to current time")

def main():
    """Start the bot."""
    global application, stop_threads
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for and handle any existing bot instances
    check_for_running_instances()
    
    # Reset all schedule timestamps to current time
    reset_all_schedules()
    
    # Create and start scheduler thread
    scheduler = threading.Thread(target=scheduler_thread)
    scheduler.daemon = True  # Thread will exit when main program exits
    scheduler.start()
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change", change_frequency))
    application.add_handler(CommandHandler("create", create_schedule))
    application.add_handler(CommandHandler("delete", delete_schedule))
    application.add_handler(CommandHandler("list", list_schedules))
    application.add_handler(CommandHandler("all", all_schedules))
    application.add_handler(CommandHandler("send", send_message))
    application.add_handler(CommandHandler("timer", timer_command))
    application.add_handler(CommandHandler("refresh", refresh_timer))
    application.add_handler(CommandHandler("control", control_bot))
    application.add_handler(CommandHandler("status", bot_status))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add unknown command handler - this must be added last!
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot started with scheduler thread for all configured schedules")
    
    try:
        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        # Stop the scheduler thread when the bot is stopped
        stop_threads = True
        logger.info("Bot stopping, waiting for threads to finish...")
        scheduler.join(timeout=5)
        logger.info("Threads stopped, bot shutdown complete")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user!")
    except Exception as e:
        logger.error(f"Bot error: {e}") 