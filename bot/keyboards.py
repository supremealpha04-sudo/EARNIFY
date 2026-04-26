from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📋 Available Tasks", callback_data="show_tasks")],
        [InlineKeyboardButton("💰 Withdraw USDT", callback_data="withdraw_menu")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="referral_info")],
        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tasks_keyboard(tasks):
    """Tasks list keyboard"""
    keyboard = []
    for task in tasks[:10]:  # Max 10 tasks per page
        emoji = task.get('icon_emoji', '💰')
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {task['title'][:30]} - ${task['reward']:.2f}", 
                callback_data=f"task_{task['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_withdrawal_keyboard():
    """Withdrawal method selection"""
    keyboard = [
        [InlineKeyboardButton("💰 USDT (BEP-20)", callback_data="withdraw_usdt_bep20")],
        [InlineKeyboardButton("ℹ️ How to Get USDT Wallet", callback_data="wallet_guide")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Admin panel keyboard (for bot admin commands)"""
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
        [InlineKeyboardButton("📋 Pending Tasks", callback_data="admin_pending_tasks")],
        [InlineKeyboardButton("💸 Pending Withdrawals", callback_data="admin_pending_withdrawals")],
        [InlineKeyboardButton("👥 User Search", callback_data="admin_search_users")],
        [InlineKeyboardButton("➕ Add Task", callback_data="admin_add_task")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(withdrawal_id):
    """Withdrawal confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_withdrawal_{withdrawal_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdrawal")]
    ]
    return InlineKeyboardMarkup(keyboard)
