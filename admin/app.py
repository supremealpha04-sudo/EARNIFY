import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client
import os
import hashlib

# Page config
st.set_page_config(
    page_title="Earnify Admin Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .stMetric {
        background-color: #1e1e2f;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .big-font {
        font-size: 30px !important;
        font-weight: bold;
    }
    .status-pending {
        background-color: #f39c12;
        color: white;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-paid {
        background-color: #27ae60;
        color: white;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-failed {
        background-color: #e74c3c;
        color: white;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    div.stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# Authentication
def authenticate():
    """Simple password authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Earnify Admin Login")
        password = st.text_input("Enter admin password:", type="password")
        
        if password == os.getenv('ADMIN_PASSWORD', 'EarnifyAdmin2024!'):
            st.session_state.authenticated = True
            st.rerun()
        elif password:
            st.error("Invalid password!")
        return False
    return True

if not authenticate():
    st.stop()

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=EARNIFY", use_column_width=True)
    st.markdown("---")
    
    menu = st.selectbox(
        "Navigation",
        ["Dashboard", "Tasks", "Users", "Withdrawals", "Analytics", "Settings"],
        format_func=lambda x: f"📊 {x}" if x == "Dashboard" else
                             f"📋 {x}" if x == "Tasks" else
                             f"👥 {x}" if x == "Users" else
                             f"💰 {x}" if x == "Withdrawals" else
                             f"📈 {x}" if x == "Analytics" else
                             f"⚙️ {x}"
    )
    
    st.markdown("---")
    st.caption(f"Logged in as Admin")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# Dashboard
if menu == "Dashboard":
    st.title("📊 Earnify Dashboard")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Get metrics
    total_users = supabase.table('users').select('telegram_id', count='exact').execute()
    active_today = supabase.table('users').select('telegram_id', count='exact')\
        .gte('last_active', datetime.now().date().isoformat()).execute()
    pending_withdrawals = supabase.table('withdrawals').select('id', count='exact')\
        .eq('status', 'pending').execute()
    total_earned = supabase.table('users').select('total_earned').execute()
    total_earned_sum = sum(u['total_earned'] for u in total_earned.data)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", f"{total_users.count:,}", delta=None)
    with col2:
        st.metric("Active Today", f"{active_today.count:,}")
    with col3:
        st.metric("Pending Withdrawals", f"${pending_withdrawals.count:,}", 
                  delta="Needs action" if pending_withdrawals.count > 0 else None)
    with col4:
        st.metric("Total Paid Out", f"${total_earned_sum:,.2f}")
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 User Growth (Last 7 Days)")
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        signups = supabase.table('users').select('created_at')\
            .gte('created_at', seven_days_ago).execute()
        
        if signups.data:
            df = pd.DataFrame(signups.data)
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_signups = df.groupby('date').size().reset_index(name='count')
            
            fig = px.line(daily_signups, x='date', y='count', 
                         title='Daily Signups', markers=True)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Earnings Overview")
        earnings = supabase.table('task_completions').select('points_awarded, completed_at')\
            .eq('status', 'approved')\
            .gte('completed_at', seven_days_ago).execute()
        
        if earnings.data:
            df = pd.DataFrame(earnings.data)
            df['date'] = pd.to_datetime(df['completed_at']).dt.date
            daily_earnings = df.groupby('date')['points_awarded'].sum().reset_index()
            
            fig = px.bar(daily_earnings, x='date', y='points_awarded',
                        title='Daily Earnings (USDT)', color='points_awarded')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    recent_withdrawals = supabase.table('withdrawals')\
        .select('*, users(first_name, username)')\
        .order('requested_at', desc=True)\
        .limit(5)\
        .execute()
    
    if recent_withdrawals.data:
        for w in recent_withdrawals.data:
            user = w['users']
            status_class = "status-pending" if w['status'] == 'pending' else "status-paid" if w['status'] == 'paid' else "status-failed"
            st.info(f"💸 **{user['first_name'] or user['username']}** requested ${w['amount']:.2f} - "
                   f"<span class='{status_class}'>{w['status'].upper()}</span>", 
                   unsafe_allow_html=True)

# Tasks Management
elif menu == "Tasks":
    st.title("📋 Task Management")
    
    # Add new task
    with st.expander("➕ Create New Task", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Task Title*", placeholder="e.g., Watch Crypto Ad")
            short_desc = st.text_input("Short Description", placeholder="Quick summary")
            description = st.text_area("Full Description*", placeholder="Detailed instructions for user")
            reward = st.number_input("Reward (USDT)*", min_value=0.01, step=0.01, value=0.05)
            task_type = st.selectbox("Task Type", ['visit', 'survey', 'video', 'social', 'install', 'daily'])
        
        with col2:
            url = st.text_input("URL (if applicable)", placeholder="https://...")
            time_required = st.number_input("Time Required (seconds)", min_value=5, value=30)
            max_completions = st.number_input("Max Completions (0=unlimited)", min_value=0, value=0)
            daily_limit = st.number_input("Daily Limit per User (0=unlimited)", min_value=0, value=0)
            requires_screenshot = st.checkbox("Require Screenshot Proof", value=False)
            icon_emoji = st.text_input("Icon Emoji", value="💰", max_chars=2)
        
        instructions = st.text_area("Step-by-Step Instructions", 
                                   placeholder="1. Click the link\n2. Wait 30 seconds\n3. Come back and click complete")
        
        expires_at = st.date_input("Expiry Date", value=datetime.now() + timedelta(days=30))
        
        if st.button("🚀 Create Task", use_container_width=True):
            if title and description:
                new_task = {
                    'title': title,
                    'short_description': short_desc,
                    'description': description,
                    'reward': reward,
                    'task_type': task_type,
                    'url': url,
                    'time_required': time_required,
                    'max_completions': max_completions if max_completions > 0 else None,
                    'daily_limit': daily_limit if daily_limit > 0 else None,
                    'requires_screenshot': requires_screenshot,
                    'instructions': instructions,
                    'icon_emoji': icon_emoji,
                    'expires_at': expires_at.isoformat(),
                    'created_by': 0  # System
                }
                
                result = supabase.table('tasks').insert(new_task).execute()
                if result.data:
                    st.success(f"✅ Task '{title}' created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create task")
            else:
                st.warning("Please fill in required fields (Title, Description)")
    
    # List existing tasks
    st.subheader("📋 Existing Tasks")
    tasks = supabase.table('tasks').select('*').order('created_at', desc=True).execute()
    
    if tasks.data:
        for task in tasks.data:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1, 1])
                with col1:
                    st.markdown(f"**{task['icon_emoji']} {task['title']}**")
                    st.caption(task.get('short_description', task['description'][:60]))
                with col2:
                    st.metric("Reward", f"${task['reward']:.2f}")
                    st.caption(f"Type: {task['task_type']}")
                with col3:
                    st.metric("Completions", f"{task['total_completions']:,}")
                    if task['max_completions']:
                        st.caption(f"Max: {task['max_completions']}")
                with col4:
                    status = "✅ Active" if task['is_active'] else "❌ Inactive"
                    st.markdown(f"**Status**\n{status}")
                with col5:
                    if st.button("🔄 Toggle", key=f"toggle_{task['id']}", use_container_width=True):
                        supabase.table('tasks').update({
                            'is_active': not task['is_active']
                        }).eq('id', task['id']).execute()
                        st.rerun()
                    if st.button("✏️ Edit", key=f"edit_{task['id']}", use_container_width=True):
                        st.session_state.edit_task = task
                        st.rerun()
                st.divider()

# User Management
elif menu == "Users":
    st.title("👥 User Management")
    
    # Search
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_term = st.text_input("🔍 Search Users", placeholder="Telegram ID, Username, or First Name")
    with search_col2:
        show_banned = st.checkbox("Show Banned Users", value=False)
    
    # Query users
    query = supabase.table('users').select('*')
    
    if search_term:
        if search_term.isdigit():
            query = query.eq('telegram_id', int(search_term))
        else:
            query = query.or_(f'username.ilike.%{search_term}%,first_name.ilike.%{search_term}%')
    
    if not show_banned:
        query = query.eq('is_banned', False)
    
    users = query.order('total_earned', desc=True).limit(50).execute()
    
    if users.data:
        st.markdown(f"**Found {len(users.data)} users**")
        
        for user in users.data:
            with st.expander(f"👤 {user['first_name'] or user['username'] or f'User_{user['telegram_id']}'} - ${user['balance']:.2f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**📋 Basic Info**")
                    st.write(f"ID: `{user['telegram_id']}`")
                    st.write(f"Username: @{user['username'] or 'N/A'}")
                    st.write(f"Joined: {user['created_at'][:10]}")
                    st.write(f"Last Active: {user['last_active'][:16] if user['last_active'] else 'N/A'}")
                
                with col2:
                    st.write("**💰 Financial**")
                    st.write(f"Balance: **${user['balance']:.2f}**")
                    st.write(f"Total Earned: ${user['total_earned']:.2f}")
                    st.write(f"Total Withdrawn: ${user['total_withdrawn']:.2f}")
                    st.write(f"Referral Code: `{user['referral_code']}`")
                
                with col3:
                    st.write("**📊 Stats**")
                    st.write(f"Daily Streak: {user['daily_streak']} days")
                    st.write(f"Banned: {'⚠️ Yes' if user['is_banned'] else '✅ No'}")
                    st.write(f"Admin: {'👑 Yes' if user['is_admin'] else '❌ No'}")
                
                # Actions
                st.write("**🛠️ Actions**")
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    adjust_amount = st.number_input(f"Adjust Balance", 
                                                   step=0.01, 
                                                   key=f"adjust_{user['telegram_id']}",
                                                   label_visibility="collapsed")
                    if st.button(f"Apply", key=f"apply_{user['telegram_id']}", use_container_width=True):
                        new_balance = user['balance'] + adjust_amount
                        supabase.table('users').update({
                            'balance': new_balance
                        }).eq('telegram_id', user['telegram_id']).execute()
                        st.success(f"Balance updated to ${new_balance:.2f}")
                        st.rerun()
                
                with action_col2:
                    if not user['is_banned']:
                        if st.button(f"🚫 Ban User", key=f"ban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({
                                'is_banned': True
                            }).eq('telegram_id', user['telegram_id']).execute()
                            st.warning(f"User {user['telegram_id']} has been banned")
                            st.rerun()
                    else:
                        if st.button(f"✅ Unban User", key=f"unban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({
                                'is_banned': False
                            }).eq('telegram_id', user['telegram_id']).execute()
                            st.success(f"User {user['telegram_id']} has been unbanned")
                            st.rerun()
                
                with action_col3:
                    if st.button(f"📜 View History", key=f"history_{user['telegram_id']}", use_container_width=True):
                        st.session_state.selected_user = user['telegram_id']
                        st.rerun()
    else:
        st.info("No users found")

# Withdrawals Management
elif menu == "Withdrawals":
    st.title("💰 Withdrawal Management")
    st.markdown("*Manual USDT (BEP-20) Processing*")
    
    # Tabs for different statuses
    tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending", "🔄 Processing", "✅ Paid", "❌ Failed"])
    
    with tab1:
        pending = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'pending')\
            .order('requested_at', asc=True)\
            .execute()
        
        if pending.data:
            for w in pending.data:
                user = w['users']
                with st.container():
                    st.markdown(f"### Withdrawal #{w['id']}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {user['first_name'] or user['username']}")
                        st.write(f"**Telegram ID:** `{w['user_id']}`")
                        st.write(f"**Amount:** 💰 **${w['amount']:.2f} USDT**")
                        st.write(f"**Network:** {w['network']}")
                    
                    with col2:
                        st.write(f"**Requested:** {w['requested_at'][:19]}")
                        st.write(f"**Wallet Address:**")
                        st.code(w['wallet_address'], language='text')
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        tx_hash = st.text_input(f"Transaction Hash", 
                                               placeholder="0x...", 
                                               key=f"tx_{w['id']}",
                                               label_visibility="collapsed")
                    
                    with col2:
                        if st.button(f"✅ Mark as Paid", key=f"pay_{w['id']}", use_container_width=True):
                            update_data = {
                                'status': 'paid',
                                'processed_at': datetime.now().isoformat(),
                                'paid_at': datetime.now().isoformat()
                            }
                            if tx_hash:
                                update_data['transaction_hash'] = tx_hash
                            
                            supabase.table('withdrawals').update(update_data)\
                                .eq('id', w['id']).execute()
                            
                            # Update user's total withdrawn
                            supabase.table('users').update({
                                'total_withdrawn': supabase.raw(f'total_withdrawn + {w["amount"]}')
                            }).eq('telegram_id', w['user_id']).execute()
                            
                            # Send notification to user
                            bot_token = os.getenv('BOT_TOKEN')
                            import requests
                            notification = f"""
✅ *Withdrawal Completed!*

💰 Amount: *${w['amount']:.2f} USDT*
🌐 Network: BEP-20
📤 Sent to: `{w['wallet_address'][:10]}...{w['wallet_address'][-6:]}`

{'📝 Transaction: `' + tx_hash + '`' if tx_hash else ''}

Thank you for using Earnify! 🎉
                            """
                            try:
                                url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                                requests.post(url, json={
                                    'chat_id': w['user_id'],
                                    'text': notification,
                                    'parse_mode': 'Markdown'
                                })
                            except:
                                pass
                            
                            st.success(f"Withdrawal #{w['id']} marked as paid!")
                            st.rerun()
                    
                    with col3:
                        if st.button(f"❌ Reject", key=f"reject_{w['id']}", use_container_width=True):
                            # Refund user
                            supabase.table('users').update({
                                'balance': supabase.raw(f'balance + {w["amount"]}')
                            }).eq('telegram_id', w['user_id']).execute()
                            
                            supabase.table('withdrawals').update({
                                'status': 'failed',
                                'admin_notes': 'Rejected by admin'
                            }).eq('id', w['id']).execute()
                            
                            st.warning(f"Withdrawal #{w['id']} rejected and refunded")
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No pending withdrawals 🎉")
    
    with tab2:
        processing = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'processing')\
            .order('processed_at', desc=True)\
            .execute()
        
        if processing.data:
            for w in processing.data:
                st.write(f"#{w['id']}: ${w['amount']:.2f} - {w['users']['first_name']} - Processing since {w['processed_at'][:16]}")
        else:
            st.info("No withdrawals in processing")
    
    with tab3:
        paid = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'paid')\
            .order('paid_at', desc=True)\
            .limit(50)\
            .execute()
        
        if paid.data:
            df = pd.DataFrame(paid.data)
            df['user_name'] = df['users'].apply(lambda x: x['first_name'] or x['username'])
            st.dataframe(df[['id', 'user_name', 'amount', 'paid_at', 'transaction_hash']], 
                        use_container_width=True)
        else:
            st.info("No paid withdrawals yet")
    
    with tab4:
        failed = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'failed')\
            .order('requested_at', desc=True)\
            .limit(50)\
            .execute()
        
        if failed.data:
            for w in failed.data:
                st.warning(f"#{w['id']}: ${w['amount']:.2f} - {w['users']['first_name']} - {w['admin_notes']}")
        else:
            st.info("No failed withdrawals")

# Analytics
elif menu == "Analytics":
    st.title("📈 Advanced Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    start_iso = datetime.combine(start_date, datetime.min.time()).isoformat()
    end_iso = datetime.combine(end_date, datetime.max.time()).isoformat()
    
    # User growth
    st.subheader("📊 User Growth")
    users_over_time = supabase.table('users').select('created_at')\
        .gte('created_at', start_iso)\
        .lte('created_at', end_iso)\
        .execute()
    
    if users_over_time.data:
        df = pd.DataFrame(users_over_time.data)
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        daily = df.groupby('date').size().reset_index(name='new_users')
        daily['cumulative'] = daily['new_users'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['cumulative'], 
                                mode='lines+markers', name='Total Users'))
        fig.add_trace(go.Bar(x=daily['date'], y=daily['new_users'], 
                            name='New Users', yaxis='y2'))
        fig.update_layout(
            title='User Growth Over Time',
            xaxis_title='Date',
            yaxis_title='Cumulative Users',
            yaxis2=dict(title='New Users', overlaying='y', side='right'),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Earnings distribution
    st.subheader("💰 Earnings Distribution")
    earnings_by_task = supabase.table('task_completions')\
        .select('tasks(title), points_awarded')\
        .eq('status', 'approved')\
        .gte('completed_at', start_iso)\
        .execute()
    
    if earnings_by_task.data:
        df = pd.DataFrame(earnings_by_task.data)
        df['task_title'] = df['tasks'].apply(lambda x: x['title'])
        task_earnings = df.groupby('task_title')['points_awarded'].sum().reset_index()
        task_earnings = task_earnings.sort_values('points_awarded', ascending=True).tail(10)
        
        fig = px.bar(task_earnings, x='points_awarded', y='task_title', 
                    orientation='h', title='Top Tasks by Earnings',
                    labels={'points_awarded': 'USDT Earned', 'task_title': 'Task'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Referral performance
    st.subheader("👥 Referral Performance")
    top_referrers = supabase.table('users')\
        .select('first_name, username, referral_earnings')\
        .gt('referral_earnings', 0)\
        .order('referral_earnings', desc=True)\
        .limit(10)\
        .execute()
    
    if top_referrers.data:
        df = pd.DataFrame(top_referrers.data)
        df['name'] = df['first_name'] + ' (@' + df['username'] + ')'
        fig = px.bar(df, x='referral_earnings', y='name', 
                    title='Top Referrers', orientation='h')
        st.plotly_chart(fig, use_container_width=True)

# Settings
elif menu == "Settings":
    st.title("⚙️ System Settings")
    
    st.info("These settings can be configured in the `.env` file")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Withdrawal Settings")
        st.code(f"""
MIN_WITHDRAWAL_USDT = {os.getenv('MIN_WITHDRAWAL_USDT', '5')}
USDT_NETWORK = {os.getenv('USDT_NETWORK', 'BEP-20')}
        """)
        
        st.subheader("👥 Admin Settings")
        st.code(f"""
ADMIN_IDS = {os.getenv('ADMIN_IDS', '123456789')}
        """)
    
    with col2:
        st.subheader("🤖 Bot Settings")
        st.code(f"""
BOT_USERNAME = {os.getenv('BOT_USERNAME', 'earnify_bot')}
ENVIRONMENT = {os.getenv('ENVIRONMENT', 'production')}
        """)
    
    st.warning("⚠️ Changes require restarting the application")

# Footer
st.markdown("---")
st.caption(f"Earnify Admin Panel v2.0 | © 2024")
