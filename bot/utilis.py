import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def validate_bep20_address(address: str) -> bool:
    """
    Validate BEP-20 wallet address
    BEP-20 addresses on BSC start with '0x' and are 42 characters long
    """
    if not address or not isinstance(address, str):
        return False
    
    # Basic BEP-20/BSC address validation
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))

def validate_trc20_address(address: str) -> bool:
    """
    Validate TRC-20 wallet address (Tron)
    TRC-20 addresses start with 'T' and are 34 characters long
    """
    if not address or not isinstance(address, str):
        return False
    
    pattern = r'^T[a-zA-Z0-9]{33}$'
    return bool(re.match(pattern, address))

def format_balance(balance: float) -> str:
    """Format balance with proper decimal places"""
    if balance < 0.01:
        return "< $0.01"
    return f"${balance:.2f}"

def format_wallet_address(address: str, show_chars: int = 6) -> str:
    """Format wallet address for display (e.g., 0x1234...5678)"""
    if not address or len(address) <= show_chars * 2:
        return address
    
    start = address[:show_chars]
    end = address[-show_chars:]
    return f"{start}...{end}"

def generate_referral_code(telegram_id: int) -> str:
    """Generate unique referral code"""
    import hashlib
    hash_obj = hashlib.md5(f"{telegram_id}{datetime.now().timestamp()}".encode())
    return f"EARN{hash_obj.hexdigest()[:8].upper()}"

def calculate_referral_earnings(amount: float, level: int = 1) -> float:
    """Calculate referral earnings based on level"""
    rates = {1: 0.10, 2: 0.05, 3: 0.02}  # 10%, 5%, 2%
    return amount * rates.get(level, 0)

def is_valid_amount(amount: str) -> Optional[float]:
    """Check if amount is valid and return float"""
    try:
        value = float(amount)
        if value <= 0:
            return None
        if value > 10000:  # Max withdrawal limit
            return None
        return round(value, 2)
    except ValueError:
        return None

def sanitize_text(text: str, max_length: int = 500) -> str:
    """Sanitize user input text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None):
    """Log user action for analytics"""
    logger.info(f"User {user_id} - {action} - {details}")

def get_time_remaining(expiry_date: datetime) -> str:
    """Get human-readable time remaining"""
    now = datetime.now()
    
    if expiry_date < now:
        return "Expired"
    
    diff = expiry_date - now
    days = diff.days
    hours = diff.seconds // 3600
    
    if days > 0:
        return f"{days} days"
    elif hours > 0:
        return f"{hours} hours"
    else:
        return "Less than an hour"

def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def parse_command_args(text: str) -> list:
    """Parse command arguments from text"""
    if not text:
        return []
    return text.split()[1:]

def create_task_completion_keyboard(task_id: int, requires_screenshot: bool = False):
    """Create inline keyboard for task completion"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    buttons = []
    
    if requires_screenshot:
        buttons.append([InlineKeyboardButton("📸 Send Screenshot", callback_data=f"task_screenshot_{task_id}")])
    else:
        buttons.append([InlineKeyboardButton("✅ Complete Task", callback_data=f"complete_task_{task_id}")])
    
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="back_to_tasks")])
    
    return InlineKeyboardMarkup(buttons)

def validate_screenshot(file_size: int) -> bool:
    """Validate screenshot file size (max 5MB)"""
    max_size = 5 * 1024 * 1024  # 5MB
    return file_size <= max_size

def get_user_rank(user_id: int, total_earned: float) -> str:
    """Get user rank based on earnings"""
    if total_earned >= 1000:
        return "👑 Legend"
    elif total_earned >= 500:
        return "💎 Diamond"
    elif total_earned >= 100:
        return "🥇 Gold"
    elif total_earned >= 50:
        return "🥈 Silver"
    elif total_earned >= 10:
        return "🥉 Bronze"
    else:
        return "🌱 Newbie"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
