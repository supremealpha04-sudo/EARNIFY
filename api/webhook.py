import os
import json
import logging
from http.server import BaseHTTPRequestHandler
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import handlers
from bot.handlers.commands import (
    start_command, tasks_command, balance_command, withdraw_command,
    daily_command, referral_command, leaderboard_command, help_command
)
from bot.handlers.callbacks import handle_callback, handle_message

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and application
bot = Bot(token=os.getenv('BOT_TOKEN'))
application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

# Register handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("tasks", tasks_command))
application.add_handler(CommandHandler("balance", balance_command))
application.add_handler(CommandHandler("withdraw", withdraw_command))
application.add_handler(CommandHandler("daily", daily_command))
application.add_handler(CommandHandler("refer", referral_command))
application.add_handler(CommandHandler("leaderboard", leaderboard_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests (Telegram webhook)"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update = Update.de_json(json.loads(post_data), bot)
            application.process_update(update)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Earnify Bot is running!')
