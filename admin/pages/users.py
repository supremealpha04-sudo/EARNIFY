import streamlit as st
import pandas as pd

def show_users(supabase):
    """Render users management page"""
    st.title("👥 User Management")
    
    # Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search Users", placeholder="Telegram ID, Username, or First Name")
    with col2:
        show_banned = st.checkbox("Show Banned Users", value=False)
    
    # Query
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
                
                with col2:
                    st.write("**💰 Financial**")
                    st.write(f"Balance: **${user['balance']:.2f}**")
                    st.write(f"Total Earned: ${user['total_earned']:.2f}")
                    st.write(f"Referral Code: `{user['referral_code']}`")
                
                with col3:
                    st.write("**📊 Stats**")
                    st.write(f"Daily Streak: {user['daily_streak']} days")
                    st.write(f"Banned: {'⚠️ Yes' if user['is_banned'] else '✅ No'}")
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    adjust_amount = st.number_input(f"Adjust Balance", step=0.01, key=f"adjust_{user['telegram_id']}", label_visibility="collapsed")
                    if st.button(f"Apply", key=f"apply_{user['telegram_id']}", use_container_width=True):
                        new_balance = user['balance'] + adjust_amount
                        supabase.table('users').update({'balance': new_balance}).eq('telegram_id', user['telegram_id']).execute()
                        st.success(f"Balance updated to ${new_balance:.2f}")
                        st.rerun()
                
                with col2:
                    if not user['is_banned']:
                        if st.button(f"🚫 Ban User", key=f"ban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({'is_banned': True}).eq('telegram_id', user['telegram_id']).execute()
                            st.rerun()
                    else:
                        if st.button(f"✅ Unban User", key=f"unban_{user['telegram_id']}", use_container_width=True):
                            supabase.table('users').update({'is_banned': False}).eq('telegram_id', user['telegram_id']).execute()
                            st.rerun()
    else:
        st.info("No users found")
