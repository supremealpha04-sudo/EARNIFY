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
    /* Main container */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Status badges */
    .status-pending {
        background-color: #f39c12;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-paid {
        background-color: #27ae60;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-processing {
        background-color: #3498db;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-failed {
        background-color: #e74c3c;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-active {
        background-color: #27ae60;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-inactive {
        background-color: #95a5a6;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Dataframes */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e1e2f 0%, #2d2d44 100%);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }
    
    /* Info/Warning/Success boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Code blocks */
    code {
        background: #1e1e2f;
        color: #10b981;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
supabase_url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
supabase_key = st.secrets.get("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY"))

if not supabase_url or not supabase_key:
    st.error("❌ Supabase credentials not found! Please add SUPABASE_URL and SUPABASE_SERVICE_KEY to secrets.")
    st.stop()

supabase = create_client(supabase_url, supabase_key)

# Authentication
def authenticate():
    """Simple password authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown('<div class="main-header"><h1 style="margin:0">🔐 Earnify Admin Login</h1></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("---")
            st.markdown("### Welcome Back")
            password = st.text_input("Enter admin password:", type="password")
            
            if st.button("Login", use_container_width=True):
                admin_password = st.secrets.get("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD", "YourSecurePassword@123!"))
                if password == admin_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Invalid password!")
            
            st.markdown("---")
            st.caption("🔒 Secure admin access only")
        return False
    return True

if not authenticate():
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("## 💰 Earnify")
    st.markdown("---")
    
    menu = st.selectbox(
        "Navigation",
        ["📊 Dashboard", "📋 Tasks", "👥 Users", "💰 Withdrawals", "📈 Analytics", "⚙️ Settings"],
        format_func=lambda x: x
    )
    
    st.markdown("---")
    st.caption(f"👑 Admin access")
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ============================================
# DASHBOARD
# ============================================
if menu == "📊 Dashboard":
    st.markdown('<div class="main-header"><h1 style="margin:0">📊 Earnify Dashboard</h1><p>Real-time statistics and insights</p></div>', unsafe_allow_html=True)
    
    # Get metrics
    total_users = supabase.table('users').select('telegram_id', count='exact').execute()
    active_today = supabase.table('users').select('telegram_id', count='exact')\
        .gte('last_active', datetime.now().date().isoformat()).execute()
    pending_withdrawals = supabase.table('withdrawals').select('id', count='exact')\
        .eq('status', 'pending').execute()
    total_earned = supabase.table('users').select('total_earned').execute()
    total_earned_sum = sum(u['total_earned'] for u in total_earned.data) if total_earned.data else 0
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">👥</div>
            <div class="metric-value">{total_users.count:,}</div>
            <div class="metric-label">Total Users</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">📱</div>
            <div class="metric-value">{active_today.count:,}</div>
            <div class="metric-label">Active Today</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">⏳</div>
            <div class="metric-value">{pending_withdrawals.count}</div>
            <div class="metric-label">Pending Withdrawals</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem;">💰</div>
            <div class="metric-value">${total_earned_sum:,.2f}</div>
            <div class="metric-label">Total Paid Out</div>
        </div>
        """, unsafe_allow_html=True)
    
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
                         title='Daily Signups', markers=True,
                         template='plotly_dark')
            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No signup data available")
    
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
                        title='Daily Earnings (USDT)', color='points_awarded',
                        template='plotly_dark', color_continuous_scale='Viridis')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No earnings data available")
    
    # Recent withdrawals
    st.subheader("🕒 Recent Withdrawal Requests")
    try:
        recent = supabase.table('withdrawals')\
            .select('id, amount, status, wallet_address, requested_at, user_id')\
            .order('requested_at', desc=True)\
            .limit(10)\
            .execute()
        
        if recent.data:
            for w in recent.data:
                status_class = f"status-{w['status']}" if w['status'] in ['pending', 'paid', 'processing', 'failed'] else "status-pending"
                st.markdown(f"""
                <div style="background: #1e1e2f; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: bold;">#{w['id']}</span>
                            <span style="margin-left: 15px;">💰 ${w['amount']:.2f}</span>
                            <span style="margin-left: 15px;">👤 User: {w['user_id']}</span>
                        </div>
                        <div>
                            <span class="{status_class}">{w['status'].upper()}</span>
                            <span style="margin-left: 15px; color: #888;">{w['requested_at'][:16]}</span>
                        </div>
                    </div>
                    <div style="margin-top: 8px; font-family: monospace; font-size: 12px; color: #888;">
                        📤 {w['wallet_address'][:30]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No withdrawals yet")
    except Exception as e:
        st.warning(f"Could not load withdrawals: {str(e)[:100]}")

# ============================================
# TASKS MANAGEMENT
# ============================================
elif menu == "📋 Tasks":
    st.markdown('<div class="main-header"><h1 style="margin:0">📋 Task Management</h1><p>Create and manage earning tasks</p></div>', unsafe_allow_html=True)
    
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
                    'is_active': True
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
                    st.caption(task.get('short_description', task['description'][:60] if task['description'] else ''))
                with col2:
                    st.metric("Reward", f"${task['reward']:.2f}")
                    st.caption(f"Type: {task['task_type']}")
                with col3:
                    st.metric("Completions", f"{task['total_completions']:,}")
                with col4:
                    status_class = "status-active" if task['is_active'] else "status-inactive"
                    status_text = "Active" if task['is_active'] else "Inactive"
                    st.markdown(f'<span class="{status_class}">{status_text}</span>', unsafe_allow_html=True)
                with col5:
                    if st.button("🔄 Toggle", key=f"toggle_{task['id']}", use_container_width=True):
                        supabase.table('tasks').update({
                            'is_active': not task['is_active']
                        }).eq('id', task['id']).execute()
                        st.rerun()
                st.divider()
    else:
        st.info("No tasks found. Create your first task above!")

# ============================================
# USERS MANAGEMENT
# ============================================
elif menu == "👥 Users":
    st.markdown('<div class="main-header"><h1 style="margin:0">👥 User Management</h1><p>Manage users, balances, and permissions</p></div>', unsafe_allow_html=True)
    
    # Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search Users", placeholder="Telegram ID, Username, or First Name")
    with col2:
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
                    st.markdown("**📋 Basic Info**")
                    st.write(f"ID: `{user['telegram_id']}`")
                    st.write(f"Username: @{user['username'] or 'N/A'}")
                    st.write(f"Joined: {user['created_at'][:10] if user['created_at'] else 'N/A'}")
                    st.write(f"Last Active: {user['last_active'][:16] if user.get('last_active') else 'N/A'}")
                
                with col2:
                    st.markdown("**💰 Financial**")
                    st.write(f"Balance: **${user['balance']:.2f}**")
                    st.write(f"Total Earned: ${user['total_earned']:.2f}")
                    st.write(f"Total Withdrawn: ${user['total_withdrawn']:.2f}")
                    st.write(f"Referral Code: `{user['referral_code']}`")
                
                with col3:
                    st.markdown("**📊 Stats**")
                    st.write(f"Daily Streak: {user['daily_streak']} days")
                    status_class = "status-active" if not user['is_banned'] else "status-failed"
                    status_text = "Active" if not user['is_banned'] else "Banned"
                    st.markdown(f"Status: <span class='{status_class}'>{status_text}</span>", unsafe_allow_html=True)
                    st.write(f"Admin: {'👑 Yes' if user.get('is_admin') else '❌ No'}")
                
                # Actions
                st.markdown("**🛠️ Actions**")
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    adjust_amount = st.number_input(f"Adjust Balance", step=0.01, key=f"adjust_{user['telegram_id']}", label_visibility="collapsed")
                    if st.button(f"Apply", key=f"apply_{user['telegram_id']}", use_container_width=True):
                        new_balance = user['balance'] + adjust_amount
                        supabase.table('users').update({'balance': new_balance}).eq('telegram_id', user['telegram_id']).execute()
                        st.success(f"Balance updated to ${new_balance:.2f}")
                        st.rerun()
                
                with action_col2:
                    if not user.get('is_banned', False):
                        if st.button(f"🚫 Ban User", key=f"ban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({'is_banned': True}).eq('telegram_id', user['telegram_id']).execute()
                            st.rerun()
                    else:
                        if st.button(f"✅ Unban User", key=f"unban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({'is_banned': False}).eq('telegram_id', user['telegram_id']).execute()
                            st.rerun()
    else:
        st.info("No users found")

# ============================================
# WITHDRAWALS MANAGEMENT
# ============================================
elif menu == "💰 Withdrawals":
    st.markdown('<div class="main-header"><h1 style="margin:0">💰 Withdrawal Management</h1><p>Manual USDT (BEP-20) Processing</p></div>', unsafe_allow_html=True)
    
    # Tabs for different statuses
    tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending", "🔄 Processing", "✅ Paid", "❌ Failed"])
    
    with tab1:
        pending = supabase.table('withdrawals')\
            .select('*')\
            .eq('status', 'pending')\
            .order('requested_at', asc=True)\
            .execute()
        
        if pending.data:
            for w in pending.data:
                with st.container():
                    st.markdown(f"### Withdrawal #{w['id']}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User ID:** `{w['user_id']}`")
                        st.write(f"**Amount:** 💰 **${w['amount']:.2f} USDT**")
                        st.write(f"**Network:** {w.get('network', 'BEP-20')}")
                    
                    with col2:
                        st.write(f"**Requested:** {w['requested_at'][:19] if w['requested_at'] else 'N/A'}")
                        st.write(f"**Wallet Address:**")
                        st.code(w['wallet_address'], language='text')
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        tx_hash = st.text_input(f"Transaction Hash", placeholder="0x...", key=f"tx_{w['id']}", label_visibility="collapsed")
                    
                    with col2:
                        if st.button(f"✅ Mark as Paid", key=f"pay_{w['id']}", use_container_width=True):
                            update_data = {
                                'status': 'paid',
                                'processed_at': datetime.now().isoformat(),
                                'paid_at': datetime.now().isoformat()
                            }
                            if tx_hash:
                                update_data['transaction_hash'] = tx_hash
                            
                            supabase.table('withdrawals').update(update_data).eq('id', w['id']).execute()
                            
                            # Update user's total withdrawn
                            supabase.table('users').update({
                                'total_withdrawn': supabase.raw(f'total_withdrawn + {w["amount"]}')
                            }).eq('telegram_id', w['user_id']).execute()
                            
                            # Send notification to user
                            bot_token = st.secrets.get("BOT_TOKEN", os.getenv("BOT_TOKEN", ""))
                            if bot_token:
                                import requests
                                notification = f"""✅ *Withdrawal Completed!*

💰 Amount: *${w['amount']:.2f} USDT*
🌐 Network: BEP-20
📤 Sent to: `{w['wallet_address'][:10]}...{w['wallet_address'][-6:]}`

{f'📝 Transaction: `{tx_hash}`' if tx_hash else ''}

Thank you for using Earnify! 🎉"""
                                try:
                                    requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', 
                                                json={'chat_id': w['user_id'], 'text': notification, 'parse_mode': 'Markdown'})
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
            .select('*')\
            .eq('status', 'processing')\
            .order('processed_at', desc=True)\
            .execute()
        
        if processing.data:
            for w in processing.data:
                st.info(f"#{w['id']}: ${w['amount']:.2f} - Processing since {w.get('processed_at', '')[:16] if w.get('processed_at') else 'N/A'}")
        else:
            st.info("No withdrawals in processing")
    
    with tab3:
        paid = supabase.table('withdrawals')\
            .select('*')\
            .eq('status', 'paid')\
            .order('paid_at', desc=True)\
            .limit(50)\
            .execute()
        
        if paid.data:
            for w in paid.data:
                st.success(f"#{w['id']}: ${w['amount']:.2f} - Paid on {w.get('paid_at', '')[:10] if w.get('paid_at') else 'N/A'}")
        else:
            st.info("No paid withdrawals yet")
    
    with tab4:
        failed = supabase.table('withdrawals')\
            .select('*')\
            .eq('status', 'failed')\
            .order('requested_at', desc=True)\
            .limit(50)\
            .execute()
        
        if failed.data:
            for w in failed.data:
                st.error(f"#{w['id']}: ${w['amount']:.2f} - {w.get('admin_notes', 'No reason provided')}")
        else:
            st.info("No failed withdrawals")

# ============================================
# ANALYTICS
# ============================================
elif menu == "📈 Analytics":
    st.markdown('<div class="main-header"><h1 style="margin:0">📈 Advanced Analytics</h1><p>Deep insights and performance metrics</p></div>', unsafe_allow_html=True)
    
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
                                mode='lines+markers', name='Total Users',
                                line=dict(color='#667eea', width=3)))
        fig.add_trace(go.Bar(x=daily['date'], y=daily['new_users'], 
                            name='New Users', yaxis='y2',
                            marker_color='#764ba2'))
        fig.update_layout(
            title='User Growth Over Time',
            xaxis_title='Date',
            yaxis_title='Cumulative Users',
            yaxis2=dict(title='New Users', overlaying='y', side='right'),
            height=500,
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No user data available")
    
    # Earnings distribution
    st.subheader("💰 Earnings Distribution")
    earnings_by_task = supabase.table('task_completions')\
        .select('tasks(title), points_awarded')\
        .eq('status', 'approved')\
        .gte('completed_at', start_iso)\
        .execute()
    
    if earnings_by_task.data:
        df = pd.DataFrame(earnings_by_task.data)
        df['task_title'] = df['tasks'].apply(lambda x: x['title'] if x else 'Unknown')
        task_earnings = df.groupby('task_title')['points_awarded'].sum().reset_index()
        task_earnings = task_earnings.sort_values('points_awarded', ascending=True).tail(10)
        
        fig = px.bar(task_earnings, x='points_awarded', y='task_title', 
                    orientation='h', title='Top Tasks by Earnings',
                    labels={'points_awarded': 'USDT Earned', 'task_title': 'Task'},
                    template='plotly_dark', color='points_awarded',
                    color_continuous_scale='Viridis')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No earnings data available")

# ============================================
# SETTINGS
# ============================================
elif menu == "⚙️ Settings":
    st.markdown('<div class="main-header"><h1 style="margin:0">⚙️ System Settings</h1><p>Configure bot and withdrawal parameters</p></div>', unsafe_allow_html=True)
    
    st.info("🔧 These settings are configured in the `.streamlit/secrets.toml` file or Vercel environment variables")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Withdrawal Settings")
        min_withdrawal = st.secrets.get("MIN_WITHDRAWAL_USDT", os.getenv("MIN_WITHDRAWAL_USDT", "5.00"))
        usdt_network = st.secrets.get("USDT_NETWORK", os.getenv("USDT_NETWORK", "BEP-20"))
        st.code(f"""
MIN_WITHDRAWAL_USDT = "{min_withdrawal}"
USDT_NETWORK = "{usdt_network}"
        """)
        
        st.subheader("👥 Admin Settings")
        admin_ids = os.getenv("ADMIN_IDS", "Not set")
        st.code(f"ADMIN_IDS = {admin_ids}")
    
    with col2:
        st.subheader("🤖 Bot Settings")
        bot_username = st.secrets.get("BOT_USERNAME", os.getenv("BOT_USERNAME", "earnify_bot"))
        environment = os.getenv("ENVIRONMENT", "production")
        st.code(f"""
BOT_USERNAME = "{bot_username}"
ENVIRONMENT = "{environment}"
        """)
    
    st.warning("⚠️ Changes require updating the secrets file and restarting the application")

# Footer
st.markdown("---")
st.markdown(f"<center><small>Earnify Admin Panel v2.0 | © 2024 | Built with ❤️</small></center>", unsafe_allow_html=True)
