import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to admin panel"""
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
        
        /* Cards */
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
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
        }
        
        .badge-success {
            background: #10b981;
            color: white;
        }
        
        .badge-warning {
            background: #f59e0b;
            color: white;
        }
        
        .badge-danger {
            background: #ef4444;
            color: white;
        }
        
        .badge-info {
            background: #3b82f6;
            color: white;
        }
        
        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th {
            background: #1e1e2f;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .data-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .data-table tr:hover {
            background: #f3f4f6;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: #1e1e2f;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #f3f4f6;
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        /* Info/Warning/Success boxes */
        .stAlert {
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Code blocks */
        code {
            background: #1e1e2f;
            color: #10b981;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        
        /* Progress bars */
        .stProgress > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(label: str, value: str, icon: str, color: str = "blue"):
    """Create a styled metric card"""
    colors = {
        "blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "green": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        "orange": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        "red": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
        "purple": "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)"
    }
    
    gradient = colors.get(color, colors["blue"])
    
    return f"""
    <div style="background: {gradient}; padding: 1.5rem; border-radius: 10px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{value}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">{label}</div>
    </div>
    """

def create_status_badge(status: str):
    """Create status badge HTML"""
    status_colors = {
        "pending": ("warning", "⏳ Pending"),
        "processing": ("info", "🔄 Processing"),
        "paid": ("success", "✅ Paid"),
        "completed": ("success", "✅ Completed"),
        "failed": ("danger", "❌ Failed"),
        "approved": ("success", "✅ Approved"),
        "rejected": ("danger", "❌ Rejected"),
        "active": ("success", "🟢 Active"),
        "inactive": ("danger", "🔴 Inactive")
    }
    
    color, text = status_colors.get(status.lower(), ("info", status))
    
    bg_colors = {
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6"
    }
    
    bg = bg_colors.get(color, "#6b7280")
    
    return f'<span style="display: inline-block; background: {bg}; color: white; padding: 4px 8px; border-radius: 20px; font-size: 12px; font-weight: 600;">{text}</span>'
