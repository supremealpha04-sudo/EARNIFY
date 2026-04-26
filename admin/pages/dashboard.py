import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client
import os

def show_dashboard(supabase):
    """Render dashboard page"""
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Users", f"{total_users.count:,}", delta=None)
    with col2:
        st.metric("📱 Active Today", f"{active_today.count:,}")
    with col3:
        st.metric("⏳ Pending Withdrawals", f"{pending_withdrawals.count:,}")
    with col4:
        st.metric("💰 Total Paid Out", f"${total_earned_sum:,.2f}")
    
    st.markdown("---")
    
    # Charts
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
    st.subheader("🕒 Recent Withdrawals")
    recent = supabase.table('withdrawals')\
        .select('*, users(first_name, username)')\
        .order('requested_at', desc=True)\
        .limit(5)\
        .execute()
    
    if recent.data:
        for w in recent.data:
            user = w['users']
            status_color = "🟡" if w['status'] == 'pending' else "🟢" if w['status'] == 'paid' else "🔴"
            st.info(f"{status_color} **{user['first_name'] or user['username']}** requested ${w['amount']:.2f} - {w['status'].upper()}")
