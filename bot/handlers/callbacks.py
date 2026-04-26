import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import DatabaseManager
from bot.keyboards import get_main_menu_keyboard, get_tasks_keyboard

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    # Navigation
    if data == "show_tasks":
        tasks = db.get_available_tasks(user_id)
        if tasks:
            await query.edit_message_text(
                f"📋 *Available Tasks* ({len(tasks)})\n\nClick any task to start earning:",
                reply_markup=get_tasks_keyboard(tasks),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "📭 No tasks available right now!\nCheck back soon!",
                reply_markup=get_main_menu_keyboard()
            )
    
    elif data == "withdraw_menu":
        user = db.get_user(user_id)
        min_withdrawal = float(os.getenv('MIN_WITHDRAWAL_USDT', '5'))
        
        if user and user['balance'] >= min_withdrawal:
            from bot.keyboards import get_withdrawal_keyboard
            await query.edit_message_text(
                f"💸 *Withdraw USDT (BEP-20)*\n\n"
                f"Balance: *${user['balance']:.2f}*\n"
                f"Minimum: *${min_withdrawal:.2f}*\n\n"
                f"Select withdrawal method:",
                reply_markup=get_withdrawal_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ *Cannot withdraw*\n\n"
                f"Current balance: ${user['balance'] if user else 0:.2f}\n"
                f"Minimum required: ${min_withdrawal:.2f}\n\n"
                f"Complete more tasks to reach minimum!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    
    elif data == "withdraw_usdt_bep20":
        await query.edit_message_text(
            "💸 *USDT (BEP-20) Withdrawal*\n\n"
            "📝 *Please send your BEP-20 wallet address*\n\n"
            "*Where to find your address:*\n"
            "• Binance: Wallet → Overview → Deposit → USDT (BEP-20)\n"
            "• Trust Wallet: Receive → USDT (BEP-20)\n"
            "• MetaMask: Add Binance Smart Chain → Receive\n\n"
            "⚠️ *Double-check your address!*\n"
            "Send the address as a single message now 👇",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_withdrawal_address'] = True
    
    elif data == "wallet_guide":
        guide_text = """
📚 *How to Get a BEP-20 USDT Wallet*

*Option 1: Trust Wallet (Mobile)*
1. Download Trust Wallet app
2. Create new wallet (save recovery phrase!)
3. Tap "Receive" → Search "USDT"
4. Select "BEP-20 (BSC)" network
5. Copy your address (starts with 0x...)

*Option 2: Binance (Exchange)*
1. Log into Binance
2. Go to Wallet → Fiat and Spot
3. Search "USDT" → Click Deposit
4. Select network "BEP-20 (BSC)"
5. Copy deposit address

*Option 3: MetaMask (Browser)*
1. Install MetaMask extension
2. Add Binance Smart Chain network
3. Add USDT token
4. Click "Receive" to get address

⚠️ *Important:* Never share your private keys! Recovery phrase is for YOU only.

Ready? Send your BEP-20 address to withdraw!
        """
        await query.edit_message_text(guide_text, parse_mode='Markdown')
    
    elif data == "my_stats":
        stats = db.get_user_stats(user_id)
        if stats:
            stats_text = f"""
📊 *Your Earnify Statistics*

💰 *Balance:* ${stats['balance']:.2f}
🏆 *Total Earned:* ${stats['total_earned']:.2f}
💸 *Total Withdrawn:* ${stats['total_withdrawn']:.2f}

👥 *Referrals:* {stats['referral_count']}
💵 *Referral Earnings:* ${stats['referral_earnings']:.2f}
🔥 *Daily Streak:* {stats['daily_streak']} days

📈 *Lifetime Stats:*
• Tasks completed: {stats.get('completed_tasks', 0)}
• Member since: {stats.get('created_at', 'N/A')[:10]}

Keep up the great work! 🚀
            """
            await query.edit_message_text(stats_text, parse_mode='Markdown')
    
    elif data == "leaderboard" or data == "refresh_leaderboard":
        top_earners = db.get_leaderboard(10)
        leaderboard_text = "🏆 *Top Earners Leaderboard*\n\n"
        
        for i, earner in enumerate(top_earners, 1):
            name = earner.get('first_name') or earner.get('username') or f'User_{i}'
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            
            leaderboard_text += f"{medal}{i}. {name[:15]} - *${earner['total_earned']:.2f}*\n"
        
        user = db.get_user(user_id)
        if user:
            higher = db.supabase.table('users')\
                .select('telegram_id', count='exact')\
                .gt('total_earned', user['total_earned'])\
                .eq('is_banned', False)\
                .execute()
            
            rank = higher.count + 1
            leaderboard_text += f"\n📊 *Your Rank:* #{rank}\n"
            leaderboard_text += f"💰 Your Total: *${user['total_earned']:.2f}*"
        
        from bot.keyboards import get_main_menu_keyboard
        await query.edit_message_text(
            leaderboard_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == "referral_info":
        await referral_command(update, context)
    
    elif data.startswith("task_"):
        task_id = int(data.split('_')[1])
        await handle_task_start(query, user_id, task_id, context)
    
    elif data == "back_to_menu":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\nChoose an option below:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    elif data == "help":
        await help_command(update, context)

async def handle_task_start(query, user_id: int, task_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Handle task start button click"""
    
    # Get task details
    task = db.supabase.table('tasks').select('*').eq('id', task_id).execute()
    
    if not task.data:
        await query.edit_message_text("❌ Task not found or has been removed.")
        return
    
    task_data = task.data[0]
    
    # Check if already completed
    existing = db.supabase.table('task_completions')\
        .select('id')\
        .eq('user_id', user_id)\
        .eq('task_id', task_id)\
        .eq('status', 'approved')\
        .execute()
    
    if existing.data:
        await query.edit_message_text(
            "✅ You've already completed this task!\n\n"
            "Try other tasks using /tasks",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Create completion record
    completion_id = db.create_task_completion(user_id, task_id, task_data.get('requires_screenshot', False))
    
    if not completion_id:
        await query.edit_message_text("❌ Error starting task. Please try again.")
        return
    
    if task_data.get('requires_screenshot'):
        # Manual verification task
        instruction_text = f"""
📸 *{task_data['title']}*

{task_data.get('instructions', task_data['description'])}

📝 *How to complete:*
1. Follow the instructions above
2. Take a screenshot showing completion
3. Send the screenshot in this chat

💰 *Reward:* ${task_data['reward']:.2f}
⏱️ *Estimated time:* {task_data['time_required']} seconds

⚠️ *Note:* Your task will be reviewed by an admin
You'll receive points once approved!

*Send your screenshot now:* 📸
        """
        
        await query.edit_message_text(instruction_text, parse_mode='Markdown')
        context.user_data['pending_task_id'] = task_id
        context.user_data['pending_completion_id'] = completion_id
        
    else:
        # Auto-approve
        db.approve_task_completion(completion_id, 0)  # 0 = system auto-approve
        
        success_text = f"""
✅ *Task Completed!*

🎉 You earned *${task_data['reward']:.2f}* USDT!

💰 New balance: Check with /balance

📋 Want more? Use /tasks for new opportunities!

💡 *Pro tip:* Claim your daily bonus with /daily!
        """
        
        await query.edit_message_text(success_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages (withdrawal addresses, screenshots)"""
    user_id = update.effective_user.id
    message = update.message
    text = message.text
    
    # Handle withdrawal address input
    if context.user_data.get('awaiting_withdrawal_address'):
        if text and text.startswith(('0x', 'T', 'bnb')):
            # Valid BEP-20 address format (0x... or other)
            wallet_address = text.strip()
            user = db.get_user(user_id)
            
            if not user:
                await message.reply_text("Please use /start first!")
                return
            
            min_withdrawal = float(os.getenv('MIN_WITHDRAWAL_USDT', '5'))
            
            if user['balance'] < min_withdrawal:
                await message.reply_text(
                    f"❌ Insufficient balance.\n"
                    f"Minimum: ${min_withdrawal:.2f}\n"
                    f"Your balance: ${user['balance']:.2f}"
                )
                del context.user_data['awaiting_withdrawal_address']
                return
            
            # Create withdrawal request
            withdrawal_id = db.create_withdrawal(user_id, user['balance'], wallet_address)
            
            if withdrawal_id:
                confirmation_text = f"""
✅ *Withdrawal Request Submitted!*

💰 Amount: *${user['balance']:.2f} USDT*
🌐 Network: *BEP-20*
📤 Wallet: `{wallet_address[:10]}...{wallet_address[-6:]}`

⏱️ *Processing time:* 24-48 hours
📋 *Request ID:* #{withdrawal_id}

*What happens next?*
1. Our team reviews your request
2. USDT will be sent to your wallet
3. You'll receive a confirmation message

⚠️ *Note:* Withdrawals are processed manually
Contact @EarnifySupport if you have questions

*Track status:* /balance
                """
                await message.reply_text(confirmation_text, parse_mode='Markdown')
                
                # Notify admins
                await notify_admins(
                    f"💰 New withdrawal request\n"
                    f"User: {user['first_name']} (ID: {user_id})\n"
                    f"Amount: ${user['balance']:.2f}\n"
                    f"Wallet: {wallet_address}"
                )
            else:
                await message.reply_text("❌ Failed to create withdrawal. Please try again.")
            
            del context.user_data['awaiting_withdrawal_address']
        
        else:
            await message.reply_text(
                "❌ *Invalid wallet address*\n\n"
                "Please send a valid BEP-20 USDT wallet address.\n"
                "It should start with '0x' (for BSC) or be a valid BEP-20 address.\n\n"
                "Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0`\n\n"
                "Send /cancel to cancel withdrawal.",
                parse_mode='Markdown'
            )
    
    # Handle screenshot for manual task verification
    elif context.user_data.get('pending_task_id') and message.photo:
        task_id = context.user_data['pending_task_id']
        completion_id = context.user_data['pending_completion_id']
        
        # Get photo file URL
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
            "⏱️ Estimated time: 12-24 hours\n"
            "💰 Reward amount will be added to your balance automatically.\n\n"
            "Thank you for your patience! 🙏",
            parse_mode='Markdown'
        )
        
        # Notify admins
        user = db.get_user(user_id)
        task = db.supabase.table('tasks').select('title').eq('id', task_id).execute()
        
        await notify_admins(
            f"📸 New task submission\n"
            f"User: {user['first_name']} (ID: {user_id})\n"
            f"Task: {task.data[0]['title'] if task.data else 'Unknown'}\n"
            f"Completion ID: #{completion_id}"
        )
        
        del context.user_data['pending_task_id']
        del context.user_data['pending_completion_id']
    
    else:
        # Unknown message
        await message.reply_text(
            "🤔 I didn't understand that.\n\n"
            "Available commands:\n"
            "/tasks - View available tasks\n"
            "/balance - Check balance\n"
            "/withdraw - Request withdrawal\n"
            "/daily - Claim daily bonus\n"
            "/refer - Get referral link\n"
            "/help - Show all commands",
            parse_mode='Markdown'
        )

async def notify_admins(message: str):
    """Send notification to all admins"""
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    bot_token = os.getenv('BOT_TOKEN')
    
    import requests
    for admin_id in admin_ids:
        try:
            url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
            data = {
                'chat_id': admin_id.strip(),
                'text': f"🔔 *Earnify Notification*\n\n{message}",
                'parse_mode': 'Markdown'
            }
            requests.post(url, json=data)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
