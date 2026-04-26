import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        try:
            result = self.supabase.table('users')\
                .select('*')\
                .eq('telegram_id', telegram_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            return None
    
    def create_user(self, telegram_id: int, username: str, first_name: str, 
                   referral_code: str, referred_by: Optional[int] = None) -> Dict:
        """Create new user"""
        try:
            user_data = {
                'telegram_id': telegram_id,
                'username': username,
                'first_name': first_name,
                'referral_code': referral_code,
                'referred_by': referred_by,
                'created_at': datetime.now().isoformat()
            }
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            return None
    
    def update_user_balance(self, telegram_id: int, amount: float, operation: str = 'add') -> bool:
        """Update user balance (add or subtract)"""
        try:
            if operation == 'add':
                self.supabase.table('users').update({
                    'balance': self.supabase.raw(f'balance + {amount}'),
                    'total_earned': self.supabase.raw(f'total_earned + {amount}')
                }).eq('telegram_id', telegram_id).execute()
            else:
                self.supabase.table('users').update({
                    'balance': self.supabase.raw(f'balance - {amount}')
                }).eq('telegram_id', telegram_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False
    
    def get_available_tasks(self, user_id: int) -> List[Dict]:
        """Get tasks available for user"""
        try:
            now = datetime.now().isoformat()
            
            # Get all active tasks
            tasks = self.supabase.table('tasks')\
                .select('*')\
                .eq('is_active', True)\
                .gte('expires_at', now)\
                .execute()
            
            # Get user's completed tasks
            completed = self.supabase.table('task_completions')\
                .select('task_id')\
                .eq('user_id', user_id)\
                .eq('status', 'approved')\
                .execute()
            
            completed_ids = [c['task_id'] for c in completed.data]
            
            # Filter available tasks
            available = [t for t in tasks.data if t['id'] not in completed_ids]
            
            # Check daily limits
            today = datetime.now().date().isoformat()
            for task in available[:]:
                if task.get('daily_limit'):
                    today_completions = self.supabase.table('task_completions')\
                        .select('id', count='exact')\
                        .eq('task_id', task['id'])\
                        .gte('completed_at', today)\
                        .execute()
                    
                    if today_completions.count >= task['daily_limit']:
                        available.remove(task)
            
            return available
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def create_task_completion(self, user_id: int, task_id: int, 
                               requires_screenshot: bool = False) -> Optional[int]:
        """Create pending task completion record"""
        try:
            # Get task reward
            task = self.supabase.table('tasks').select('reward').eq('id', task_id).execute()
            if not task.data:
                return None
            
            completion_data = {
                'user_id': user_id,
                'task_id': task_id,
                'status': 'pending',
                'points_awarded': task.data[0]['reward'],
                'completed_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('task_completions').insert(completion_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            logger.error(f"Error creating task completion: {e}")
            return None
    
    def approve_task_completion(self, completion_id: int, admin_id: int) -> bool:
        """Approve task completion and award points"""
        try:
            # Get completion details
            completion = self.supabase.table('task_completions')\
                .select('*, tasks(reward)')\
                .eq('id', completion_id)\
                .execute()
            
            if not completion.data or completion.data[0]['status'] != 'pending':
                return False
            
            # Update completion status
            self.supabase.table('task_completions').update({
                'status': 'approved',
                'approved_at': datetime.now().isoformat(),
                'approved_by': admin_id
            }).eq('id', completion_id).execute()
            
            # Update task total completions
            task_id = completion.data[0]['task_id']
            self.supabase.table('tasks').update({
                'total_completions': self.supabase.raw('total_completions + 1')
            }).eq('id', task_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error approving task: {e}")
            return False
    
    def create_withdrawal(self, user_id: int, amount: float, wallet_address: str) -> Optional[int]:
        """Create withdrawal request"""
        try:
            withdrawal_data = {
                'user_id': user_id,
                'amount': amount,
                'wallet_address': wallet_address,
                'network': 'BEP-20',
                'method': 'usdt_bep20',
                'status': 'pending',
                'requested_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('withdrawals').insert(withdrawal_data).execute()
            
            if result.data:
                # Deduct balance immediately
                self.update_user_balance(user_id, amount, 'subtract')
                return result.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Error creating withdrawal: {e}")
            return None
    
    def get_daily_bonus(self, user_id: int) -> Dict:
        """Get daily bonus for user"""
        try:
            user = self.get_user(user_id)
            if not user:
                return {'amount': 0, 'streak': 0}
            
            today = datetime.now().date()
            last_daily = user.get('last_daily')
            
            # Calculate streak
            streak = user.get('daily_streak', 0)
            if last_daily:
                last_date = datetime.fromisoformat(last_daily).date()
                if (today - last_date).days == 1:
                    streak += 1
                elif (today - last_date).days > 1:
                    streak = 1
            else:
                streak = 1
            
            # Get bonus amount
            day_num = min(streak, 7)
            bonus = self.supabase.table('daily_bonuses')\
                .select('base_reward, bonus_multiplier')\
                .eq('day_number', day_num)\
                .execute()
            
            if bonus.data:
                amount = bonus.data[0]['base_reward'] * bonus.data[0]['bonus_multiplier']
            else:
                amount = 0.05
            
            return {'amount': amount, 'streak': streak}
        except Exception as e:
            logger.error(f"Error getting daily bonus: {e}")
            return {'amount': 0, 'streak': 0}
    
    def claim_daily_bonus(self, user_id: int) -> bool:
        """Claim and award daily bonus"""
        try:
            bonus = self.get_daily_bonus(user_id)
            amount = bonus['amount']
            streak = bonus['streak']
            
            # Update user
            self.supabase.table('users').update({
                'balance': self.supabase.raw(f'balance + {amount}'),
                'total_earned': self.supabase.raw(f'total_earned + {amount}'),
                'daily_streak': streak,
                'last_daily': datetime.now().date().isoformat()
            }).eq('telegram_id', user_id).execute()
            
            # Log activity
            self.supabase.table('user_activity').insert({
                'user_id': user_id,
                'action_type': 'daily_bonus',
                'metadata': {'streak': streak, 'amount': amount}
            }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error claiming daily bonus: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            user = self.get_user(user_id)
            if not user:
                return {}
            
            # Get referral count
            referrals = self.supabase.table('users')\
                .select('telegram_id', count='exact')\
                .eq('referred_by', user_id)\
                .execute()
            
            # Get referral earnings
            ref_earnings = self.supabase.table('referral_earnings')\
                .select('amount')\
                .eq('referrer_id', user_id)\
                .execute()
            
            total_ref_earnings = sum(e['amount'] for e in ref_earnings.data)
            
            return {
                'balance': user['balance'],
                'total_earned': user['total_earned'],
                'total_withdrawn': user['total_withdrawn'],
                'referral_count': referrals.count,
                'referral_earnings': total_ref_earnings,
                'daily_streak': user['daily_streak'],
                'completed_tasks': user.get('total_completions', 0)
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top earners leaderboard"""
        try:
            result = self.supabase.table('users')\
                .select('first_name, username, total_earned')\
                .eq('is_banned', False)\
                .order('total_earned', desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def add_referral_bonus(self, referrer_id: int, new_user_id: int) -> bool:
        """Add referral bonus"""
        try:
            bonus_amount = 0.10  # $0.10 for referral signup
            
            # Add bonus to referrer
            self.update_user_balance(referrer_id, bonus_amount, 'add')
            
            # Record referral earning
            self.supabase.table('referral_earnings').insert({
                'referrer_id': referrer_id,
                'referred_user_id': new_user_id,
                'amount': bonus_amount,
                'level': 1
            }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error adding referral bonus: {e}")
            return False
