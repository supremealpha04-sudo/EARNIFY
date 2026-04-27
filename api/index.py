import os
import json
import logging
from http.server import BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import sys
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import bot modules
from bot.database import DatabaseManager
from bot.keyboards import get_main_menu_keyboard, get_tasks_keyboard, get_withdrawal_keyboard
from bot.utils import validate_bep20_address, format_balance

# Initialize database
db = DatabaseManager()

# Bot token
TOKEN = os.getenv('BOT_TOKEN')
application = Application.builder().token(TOKEN).build()

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    telegram_id = user.id
    
    existing_user = db.get_user(telegram_id)
    
    if not existing_user:
        referral_code = f"EARN{telegram_id % 1000000:06d}"
        
        # Check referral
        referred_by = None
        if context.args and len(context.args) > 0:
            referrer = db.supabase.table('users').select('telegram_id').eq('referral_code', context.args[0]).execute()
            if referrer.data:
                referred_by = referrer.data[0]['telegram_id']
                db.add_referral_bonus(referred_by, telegram_id)
        
        # Create user
        db.create_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            referral_code=referral_code,
            referred_by=referred_by
        )
        
        welcome_text = f"""🎉 *Welcome to Earnify, {user.first_name}!*

Turn simple tasks into USDT rewards!

✨ *How it works:*
• Complete easy tasks (visits, surveys, social)
• Earn USDT instantly
• Withdraw to your BEP-20 wallet

🚀 *Quick Start:*
Click "Available Tasks" below to begin earning!

💡 *Pro tip:* Invite friends to earn 10% of their earnings!"""
    else:
        welcome_text = f"""👋 *Welcome back, {user.first_name}!*

💰 Balance: *${existing_user['balance']:.2f}*
🏆 Total Earned: *${existing_user['total_earned']:.2f}*
🔥 Daily Streak: {existing_user['daily_streak']} days

Ready to earn more? Choose an option below 👇"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available tasks"""
    user_id = update.effective_user.id
    
    user = db.get_user(user_id)
    if user and user.get('is_banned'):
        await update.message.reply_text("❌ You have been banned from using Earnify.")
        return
    
    tasks = db.get_available_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text(
            "📭 *No tasks available right now!*\n\n"
            "New tasks are added daily.\n"
            "Check back soon or invite friends for bonus rewards!",
            parse_mode='Markdown'
        )
        return
    
    tasks_text = f"📋 *Available Tasks* ({len(tasks)} found)\n\n"
    for task in tasks[:5]:
        tasks_text += f"{task.get('icon_emoji', '💰')} *{task['title']}*\n"
        tasks_text += f"└ 💰 ${task['reward']:.2f} | ⏱️ {task['time_required']}s\n\n"
    
    await update.message.reply_text(
        tasks_text,
        reply_markup=get_tasks_keyboard(tasks),
        parse_mode='Markdown'
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user balance"""
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text("Please use /start first!")
        return
    
    balance_text = f"""
💰 *Your Earnify Wallet*

┌─────────────────────────
│ 💵 *Balance:* ${stats['balance']:.2f} USDT
│ 🏆 *Total Earned:* ${stats['total_earned']:.2f}
│ 💸 *Total Withdrawn:* ${stats['total_withdrawn']:.2f}
├─────────────────────────
│ 👥 *Referrals:* {stats['referral_count']}
│ 💰 *Referral Earnings:* ${stats['referral_earnings']:.2f}
│ 🔥 *Daily Streak:* {stats['daily_streak']} days
└─────────────────────────

⚡ *Minimum withdrawal:* $5 USDT
🌐 *Network:* BEP-20

Use /withdraw to cash out your earnings!
    """
    
    keyboard = [[InlineKeyboardButton("💸 Withdraw Now", callback_data="withdraw_menu")]]
    await update.message.reply_text(balance_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal request"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please use /start first!")
        return
    
    min_withdrawal = float(os.getenv('MIN_WITHDRAWAL_USDT', '5'))
    
    if user['balance'] < min_withdrawal:
        await update.message.reply_text(
            f"❌ *Insufficient balance*\n\n"
            f"Current: ${user['balance']:.2f}\n"
            f"Minimum: ${min_withdrawal:.2f}\n\n"
            f"Complete more tasks to reach minimum!",
            parse_mode='Markdown'
        )
        return
    
    # Check pending withdrawals
    pending = db.supabase.table('withdrawals').select('id', count='exact')\
        .eq('user_id', user_id).eq('status', 'pending').execute()
    
    if pending.count > 0:
        await update.message.reply_text(
            "⚠️ *You already have a pending withdrawal*\n\n"
            "Please wait for it to be processed.",
            parse_mode='Markdown'
        )
        return
    
    withdrawal_text = f"""
💸 *Withdraw USDT (BEP-20)*

💰 Available: *${user['balance']:.2f} USDT*
⚡ Minimum: *${min_withdrawal:.2f}*

📝 *Instructions:*
Send your BEP-20 USDT wallet address.
Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0`

⚠️ *Double-check your address!*

*Send your BEP-20 wallet address now:*
    """
    
    await update.message.reply_text(withdrawal_text, parse_mode='Markdown')
    context.user_data['awaiting_withdrawal'] = True

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily bonus"""
    user_id = update.effective_user.id
    
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("Please use /start first!")
        return
    
    last_daily = user.get('last_daily')
    today = __import__('datetime').datetime.now().date()
    
    if last_daily:
        last_date = __import__('datetime').datetime.fromisoformat(last_daily).date()
        if last_date == today:
            await update.message.reply_text(
                f"✅ *Daily bonus already claimed today!*\n\n"
                f"Current streak: {user['daily_streak']} days\n"
                f"Come back tomorrow for bigger rewards!",
                parse_mode='Markdown'
            )
            return
    
    # Claim bonus
    if db.claim_daily_bonus(user_id):
        bonus = db.get_daily_bonus(user_id)
        
        await update.message.reply_text(
            f"🎁 *Daily Bonus Claimed!*\n\n"
            f"🔥 Streak: *{bonus['streak']} days*\n"
            f"💰 Bonus: *${bonus['amount']:.2f}*\n\n"
            f"Keep your streak alive for maximum rewards!",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Failed to claim bonus. Please try again later.")

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral info"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please use /start first!")
        return
    
    referral_code = user['referral_code']
    bot_username = os.getenv('BOT_USERNAME', 'earnify_bot')
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    stats = db.get_user_stats(user_id)
    
    referral_text = f"""
👥 *Earnify Referral Program*

*How it works:*
• Share your unique link with friends
• Earn *10%* of everything they earn

🔗 *Your Referral Link:*
`{referral_link}`

📊 *Your Stats:*
• Referrals: {stats['referral_count']}
• Earnings: *${stats['referral_earnings']:.2f}*

🏆 *Referral Tiers:*
5 friends → Unlock bonus tasks
10 friends → +5% earnings boost

*Copy your link and start sharing!* 🚀
    """
    
    keyboard = [[InlineKeyboardButton("📤 Share Link", callback_data=f"share_{referral_code}")]]
    await update.message.reply_text(referral_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top earners"""
    top_earners = db.get_leaderboard(10)
    
    if not top_earners:
        await update.message.reply_text("No users found yet. Be the first!")
        return
    
    leaderboard_text = "🏆 *Top Earners Leaderboard*\n\n"
    
    for i, earner in enumerate(top_earners, 1):
        name = earner.get('first_name') or earner.get('username') or f'User_{i}'
        medal = "🥇 " if i == 1 else "🥈 " if i == 2 else "🥉 " if i == 3 else ""
        leaderboard_text += f"{medal}{i}. {name[:15]} - *${earner['total_earned']:.2f}*\n"
    
    # Get user rank
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        higher = db.supabase.table('users').select('telegram_id', count='exact')\
            .gt('total_earned', user['total_earned']).eq('is_banned', False).execute()
        rank = higher.count + 1
        leaderboard_text += f"\n📊 *Your Rank:* #{rank}\n"
        leaderboard_text += f"💰 Your Total: *${user['total_earned']:.2f}*"
    
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = """
❓ *Earnify Help Center*

*Commands:*
/tasks - View available tasks
/balance - Check your balance
/withdraw - Request payout
/daily - Claim daily bonus
/refer - Get referral link
/leaderboard - Top earners
/help - Show this message

*Task Types:*
• 🌐 Visit - Stay on website
• 📺 Video - Watch short ad
• 📱 Social - Follow on social media
• ✨ Daily - Daily streak bonus

*Withdrawals:*
• Minimum: $5 USDT
• Network: BEP-20 only
• Processing: 24-48 hours

*Need help?* Contact @EarnifySupport
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============================================
# CALLBACK HANDLERS
# ============================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "show_tasks":
        tasks = db.get_available_tasks(user_id)
        if tasks:
            await query.edit_message_text(
                f"📋 *Available Tasks* ({len(tasks)})\n\nClick any task to start:",
                reply_markup=get_tasks_keyboard(tasks),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("📭 No tasks available right now!")
    
    elif data == "withdraw_menu":
        user = db.get_user(user_id)
        if user and user['balance'] >= 5:
            await query.edit_message_text(
                "💸 *Send your BEP-20 wallet address:*\n\n"
                "Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0`",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_withdrawal'] = True
        else:
            await query.edit_message_text("❌ Insufficient balance for withdrawal")
    
    elif data == "referral_info":
        await referral_command(update, context)
    
    elif data == "my_stats":
        await balance_command(update, context)
    
    elif data == "leaderboard":
        await leaderboard_command(update, context)
    
    elif data == "help":
        await help_command(update, context)
    
    elif data.startswith("task_"):
        task_id = int(data.split('_')[1])
        task = db.supabase.table('tasks').select('*').eq('id', task_id).execute()
        
        if task.data:
            task_data = task.data[0]
            
            # Create completion record
            completion_id = db.create_task_completion(user_id, task_id, task_data.get('requires_screenshot', False))
            
            if completion_id:
                # Auto-approve for simple tasks
                if not task_data.get('requires_screenshot'):
                    db.approve_task_completion(completion_id, 0)
                    await query.edit_message_text(
                        f"✅ *Task Completed!*\n\n"
                        f"You earned *${task_data['reward']:.2f}* USDT!\n\n"
                        f"Use /tasks for more opportunities!",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        f"📸 *{task_data['title']}*\n\n"
                        f"{task_data['instructions']}\n\n"
                        f"💰 Reward: ${task_data['reward']:.2f}\n\n"
                        f"*Send your screenshot now:*",
                        parse_mode='Markdown'
                    )
                    context.user_data['pending_task_id'] = task_id
                    context.user_data['pending_completion_id'] = completion_id
    
    elif data.startswith("share_"):
        code = data.split('_')[1]
        bot_username = os.getenv('BOT_USERNAME', 'earnify_bot')
        link = f"https://t.me/{bot_username}?start={code}"
        await query.edit_message_text(f"🔗 *Your Referral Link:*\n\n`{link}`", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages"""
    user_id = update.effective_user.id
    message = update.message
    text = message.text
    
    # Handle withdrawal address
    if context.user_data.get('awaiting_withdrawal'):
        if text and text.startswith('0x') and len(text) == 42:
            wallet_address = text.strip()
            user = db.get_user(user_id)
            
            if user and user['balance'] >= 5:
                withdrawal_id = db.create_withdrawal(user_id, user['balance'], wallet_address)
                
                if withdrawal_id:
                    await message.reply_text(
                        f"✅ *Withdrawal Request Submitted!*\n\n"
                        f"💰 Amount: *${user['balance']:.2f} USDT*\n"
                        f"📤 Wallet: `{wallet_address[:10]}...{wallet_address[-6:]}`\n\n"
                        f"⏱️ Processing time: 24-48 hours\n\n"
                        f"You'll receive confirmation when sent!",
                        parse_mode='Markdown'
                    )
                    
                    # Notify admins
                    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
                    for admin_id in admin_ids:
                        try:
                            await application.bot.send_message(
                                chat_id=int(admin_id),
                                text=f"💰 *New Withdrawal Request*\n\n"
                                     f"User ID: {user_id}\n"
                                     f"Amount: ${user['balance']:.2f}\n"
                                     f"Wallet: {wallet_address}",
                                parse_mode='Markdown'
                            )
                        except:
                            pass
                else:
                    await message.reply_text("❌ Failed to create withdrawal. Please try again.")
            else:
                await message.reply_text("❌ Insufficient balance for withdrawal.")
            
            del context.user_data['awaiting_withdrawal']
        else:
            await message.reply_text(
                "❌ *Invalid wallet address*\n\n"
                "Please send a valid BEP-20 address.\n"
                "It should start with '0x' and be 42 characters long.\n\n"
                "Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0`",
                parse_mode='Markdown'
            )
    
    # Handle screenshot for manual tasks
    elif context.user_data.get('pending_task_id') and message.photo:
        task_id = context.user_data['pending_task_id']
        completion_id = context.user_data['pending_completion_id']
        
        # Get photo URL
        photo = message.photo[-1]
        file = await photo.get_file()
        photo_url = file.file_path
        
        # Update completion with screenshot
        db.supabase.table('task_completions').update({
            'screenshot_url': photo_url
        }).eq('id', completion_id).execute()
        
        await message.reply_text(
            "📸 *Screenshot received!*\n\n"
            "Your task is pending admin review.\n"
            "You'll receive your reward once approved.\n\n"
            "Thank you for your patience! 🙏",
            parse_mode='Markdown'
        )
        
        # Notify admins
        admin_ids = os.getenv('ADMIN_IDS', '').split(',')
        for admin_id in admin_ids:
            try:
                await application.bot.send_message(
                    chat_id=int(admin_id),
                    text=f"📸 *New Task Submission*\n\nUser ID: {user_id}\nTask ID: {task_id}",
                    parse_mode='Markdown'
                )
            except:
                pass
        
        del context.user_data['pending_task_id']
        del context.user_data['pending_completion_id']
    
    else:
        await message.reply_text(
            "🤔 *Unknown command*\n\n"
            "Use /help to see available commands.",
            parse_mode='Markdown'
        )

# ============================================
# REGISTER HANDLERS
# ============================================

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

# ============================================
# VERCEL HANDLER
# ============================================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Earnify Bot is running! Full version deployed.')
    
    def do_POST(self):
        """Handle Telegram webhook"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = Update.de_json(json.loads(post_data), application.bot)
                
                # Run the update handler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.process_update(update))
                loop.close()
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
