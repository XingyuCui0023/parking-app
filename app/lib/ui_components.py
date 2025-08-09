# app/lib/ui_components.py
import streamlit as st
from datetime import datetime

def apply_safe_custom_css():
    """应用不影响侧边栏的安全CSS样式"""
    st.markdown("""
    <style>
    /* 自定义标题样式 */
    .custom-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .custom-subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 卡片样式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* 可点击卡片样式 */
    .clickable-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
        border-color: #3b82f6;
    }
    
    /* 改进的度量卡片样式 */
    div[data-testid="metric-container"] {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    }
    
    /* 安全的按钮样式 - 只针对主要内容区域，避免影响侧边栏 */
    .main .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .main .stButton > button:hover {
        background: linear-gradient(90deg, #2563eb, #1e40af);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* 隐藏 Streamlit 部署按钮 */
    .stDeployButton {display: none;}
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .custom-title {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def create_header(title, subtitle=None, icon=None):
    """创建页面标题"""
    if icon:
        title_with_icon = f"{icon} {title}"
    else:
        title_with_icon = title
    
    st.markdown(f'<h1 class="custom-title">{title_with_icon}</h1>', unsafe_allow_html=True)
    
    if subtitle:
        st.markdown(f'<p class="custom-subtitle">{subtitle}</p>', unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, delta_color="normal"):
    """创建度量卡片"""
    delta_html = ""
    if delta:
        color = "#28a745" if delta_color == "normal" else "#dc3545"
        delta_html = f'<div style="color: {color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
    
    return f"""
    <div class="metric-card">
        <div style="font-size: 2rem; font-weight: bold; color: #1f2937;">{value}</div>
        <div style="color: #6b7280; font-size: 1rem;">{label}</div>
        {delta_html}
    </div>
    """

def create_status_badge(status, is_occupied=None):
    """创建状态徽章"""
    if is_occupied is True:
        color = "#dc3545"
        text = "Occupied"
    elif is_occupied is False:
        color = "#28a745" 
        text = "Available"
    else:
        color = "#6c757d"
        text = status
    
    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    ">{text}</span>
    """

def create_info_box(title, content, icon="ℹ️"):
    """创建美化的信息框"""
    st.markdown(f"""
    <div style="
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981);
        "></div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="
                font-size: 2rem; 
                margin-right: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">{icon}</div>
            <h3 style="
                margin: 0; 
                color: #1f2937; 
                font-size: 1.5rem;
                font-weight: 600;
            ">{title}</h3>
        </div>
        <p style="
            margin: 0; 
            color: #4b5563; 
            line-height: 1.6;
            font-size: 1rem;
        ">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_footer():
    """创建页脚"""
    current_year = datetime.now().year
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0; margin-top: 3rem; border-top: 1px solid #e5e7eb; color: #6b7280;">
        <p>© {current_year} Melbourne Parking Insights | Built with ❤️ using Streamlit</p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">
            Data source: Melbourne Open Data Platform
        </p>
    </div>
    """, unsafe_allow_html=True)