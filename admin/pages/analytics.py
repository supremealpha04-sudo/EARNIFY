import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_analytics(supabase):
    """Render analytics page"""
    st.title("📈 Advanced Analytics")
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    start_iso = datetime.combine(start_date, datetime.min.time()).isoformat()
    end_iso = datetime.combine(end_date, datetime.max.time()).isoformat()
    
    # User growth
    st.subheader("📊 User Growth")
    users = supabase.table('users').select('created_at')\
        .gte('created_at', start_iso).lte('created_at', end_iso).execute()
    
    if users.data:
        df = pd.DataFrame(users.data)
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        daily = df.groupby('date').size().reset_index(name='new_users')
        daily['cumulative'] = daily['new_users'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['cumulative'], mode='lines+markers', name='Total Users'))
        fig.add_trace(go.Bar(x=daily['date'], y=daily['new_users'], name='New Users', yaxis='y2'))
        fig.update_layout(height=500, xaxis_title='Date', yaxis_title='Cumulative', yaxis2=dict(title='New Users', overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)
    
    # Top tasks
    st.subheader("💰 Top Performing Tasks")
    tasks = supabase.table('task_completions')\
        .select('tasks(title), points_awarded')\
        .eq('status', 'approved')\
        .execute()
    
    if tasks.data:
        df = pd.DataFrame(tasks.data)
        df['task_title'] = df['tasks'].apply(lambda x: x['title'])
        task_earnings = df.groupby('task_title')['points_awarded'].sum().reset_index()
        task_earnings = task_earnings.sort_values('points_awarded', ascending=True).tail(10)
        
        fig = px.bar(task_earnings, x='points_awarded', y='task_title', orientation='h')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
