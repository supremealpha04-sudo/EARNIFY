import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def show_tasks(supabase):
    """Render tasks management page"""
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
                    'created_by': 0
                }
                
                result = supabase.table('tasks').insert(new_task).execute()
                if result.data:
                    st.success(f"✅ Task '{title}' created successfully!")
                    st.rerun()
            else:
                st.warning("Please fill in required fields")
    
    # List tasks
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
                with col4:
                    status = "✅ Active" if task['is_active'] else "❌ Inactive"
                    st.markdown(f"**Status**\n{status}")
                with col5:
                    if st.button("🔄 Toggle", key=f"toggle_{task['id']}", use_container_width=True):
                        supabase.table('tasks').update({
                            'is_active': not task['is_active']
                        }).eq('id', task['id']).execute()
                        st.rerun()
                st.divider()
    else:
        st.info("No tasks found. Create your first task above!")
