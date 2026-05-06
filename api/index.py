import os
import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Load ad credentials from environment
ADSTERRA_API_KEY = os.getenv('ADSTERRA_API_KEY', '')
ADSTERRA_ZONE_ID = os.getenv('ADSTERRA_ZONE_ID', '')
ADSTERRA_URL = os.getenv('ADSTERRA_POPUNDER_URL', '')
ADS_DAILY_LIMIT = int(os.getenv('ADS_DAILY_LIMIT_PER_USER', 30))
USER_REWARD = float(os.getenv('USER_REWARD_PER_AD', 0.002))

class AdManager:
    def __init__(self):
        self.adsterra_url = ADSTERRA_URL
    
    def get_active_ad(self):
        if self.adsterra_url:
            return {'url': self.adsterra_url, 'network': 'Adsterra'}
        return {'url': 'https://example.com/demo-ad', 'network': 'Demo'}
    
    def log_ad_view(self, user_id, ad_type, reward_earned):
        supabase.table('ad_views').insert({
            'user_id': user_id,
            'ad_type': ad_type,
            'reward_earned': reward_earned,
            'created_at': datetime.now().isoformat()
        }).execute()

async def handle_ad_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_data: dict):
    query = update.callback_query
    user_id = update.effective_user.id
    today = datetime.now().date().isoformat()
    daily_views = supabase.table('ad_views').select('id', count='exact')\
        .eq('user_id', user_id).gte('created_at', today).execute()
    if daily_views.count >= ADS_DAILY_LIMIT:
        await query.edit_message_text(f"❌ Daily ad limit reached ({daily_views.count}/{ADS_DAILY_LIMIT}). Come back tomorrow.", parse_mode='Markdown')
        return
    ad_manager = AdManager()
    ad = ad_manager.get_active_ad()
    await query.edit_message_text(
        f"📺 *Watch Ad to Earn*\n💰 Reward: ${USER_REWARD:.3f} USDT\n📊 Today: {daily_views.count+1}/{ADS_DAILY_LIMIT}\n\n🔗 [Click Here to Watch]({ad['url']})\n\n⏱️ Wait 30 seconds, then click **Complete**.",
        parse_mode='Markdown', disable_web_page_preview=True
    )
    context.user_data['ad_session'] = {'reward': USER_REWARD, 'start_time': datetime.now()}
    await asyncio.sleep(30)
    if context.user_data.get('ad_session'):
        keyboard = [[InlineKeyboardButton("✅ Complete & Earn", callback_data=f"complete_ad")]]
        await update.effective_message.reply_text("✅ Time's up! Click below to receive your reward.", reply_markup=InlineKeyboardMarkup(keyboard))

async def complete_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    session = context.user_data.pop('ad_session', {})
    if not session:
        await query.edit_message_text("❌ No active ad session. Start a new ad task from /tasks.", parse_mode='Markdown')
        return
    start_time = session.get('start_time')
    if start_time and (datetime.now() - start_time).seconds < 25:
        await query.edit_message_text("⏱️ Please watch the full 30 seconds before completing.", parse_mode='Markdown')
        return
    reward = session.get('reward', USER_REWARD)
    supabase.table('users').update({
        'balance': supabase.raw(f'balance + {reward}'),
        'total_earned': supabase.raw(f'total_earned + {reward}')
    }).eq('telegram_id', user_id).execute()
    AdManager().log_ad_view(user_id, 'popunder', reward)
    await query.edit_message_text(f"✅ Ad completed! You earned *${reward:.3f} USDT*.", parse_mode='Markdown')

# Register the callback handler (add to your existing handlers)
application.add_handler(CallbackQueryHandler(complete_ad, pattern='complete_ad'))
