import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

# Import handlers
from bot.handlers.commands import (
    start_command, tasks_command, balance_command, withdraw_command,
    daily_command, referral_command, leaderboard_command, help_command
)
from bot.handlers.callbacks import handle_callback, handle_message

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot"""
    # Create application
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("withdraw", withdraw_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("refer", referral_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add message handler (for wallet addresses and screenshots)
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    
    # Start bot
    logger.info("Starting Earnify bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
