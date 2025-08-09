import streamlit as st
from pathlib import Path
from lib.ui_components import apply_safe_custom_css, create_footer

st.set_page_config(page_title="Melbourne Parking Insights", page_icon="🅿️", layout="wide")

# 应用安全的自定义样式
apply_safe_custom_css()

def create_gradient_title(title, subtitle):
    """创建渐变标题"""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
    ">
        <h1 style="font-size: 3rem; margin: 0 0 1rem 0;">{title}</h1>
        <p style="font-size: 1.2rem; margin: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def create_section_title(title):
    """创建区域标题"""
    st.markdown(f"""
    <h2 style='
        text-align: center;
        font-size: 2.5rem;
        margin: 3rem 0 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    '>{title}</h2>
    """, unsafe_allow_html=True)

def create_feature_card(icon, title, description, gradient):
    """创建功能卡片"""
    st.markdown(f"""
    <div style="
        padding: 2rem;
        background: linear-gradient(135deg, {gradient});
        border-radius: 15px;
        color: white;
        text-align: center;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="margin: 0 0 1rem 0; font-size: 1.3rem;">{title}</h3>
        <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def create_stat_card(icon, value, title, subtitle, color):
    """创建统计卡片"""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1.5rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">{icon}</div>
        <div style="font-size: 2rem; font-weight: 700; color: {color}; margin-bottom: 0.5rem;">{value}</div>
        <div style="font-size: 1rem; font-weight: 600; color: #1f2937; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 0.8rem; color: #6b7280;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def create_info_card(icon, title, description, gradient):
    """创建信息卡片"""
    st.markdown(f"""
    <div style="
        padding: 2rem;
        background: linear-gradient(135deg, {gradient});
        border-radius: 15px;
        color: white;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="font-size: 2rem; margin-right: 1rem;">{icon}</div>
            <h3 style="margin: 0; font-size: 1.3rem;">{title}</h3>
        </div>
        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; opacity: 0.9;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)

# 页面标题
create_gradient_title("Melbourne Parking Insights", "Smart parking solutions for a smarter city")

# 图片展示区域
CURRENT_DIR = Path(__file__).parent
IMAGE_PATH = CURRENT_DIR / "assets" / "home.png"

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    # 图片展示
    if IMAGE_PATH.exists():
        st.image(str(IMAGE_PATH), use_container_width=True, caption="Melbourne CBD Parking Overview")
    else:
        st.info("Melbourne Parking - Smart Parking Solutions")

# 功能介绍卡片
create_section_title("What You Can Do")

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    create_feature_card(
        "🚗", 
        "Car Ownership Analysis",
        "Compare Victoria with other states and understand vehicle registration trends from 2016-2020.",
        "#667eea 0%, #764ba2 100%"
    )

with col2:
    create_feature_card(
        "📈", 
        "Population Growth",
        "Explore Victoria's population trends from 2001-2021 and understand urban growth patterns.",
        "#11998e 0%, #38ef7d 100%"
    )

with col3:
    create_feature_card(
        "🗺️", 
        "Smart Parking Search",
        "Find available parking spots with interactive maps and navigation assistance.",
        "#8b5cf6 0%, #ec4899 100%"
    )

# 快速统计
create_section_title("Quick Stats")

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    create_stat_card("📊", "3+", "Data Sources", "Live APIs", "#667eea")

with col2:
    create_stat_card("📅", "20+", "Years Covered", "2001-2021", "#11998e")

with col3:
    create_stat_card("🅿️", "3K+", "Parking Bays", "CBD Area", "#8b5cf6")

with col4:
    create_stat_card("🇦🇺", "8", "States Analyzed", "Australia-wide", "#f59e0b")

# 信息区域
st.markdown('<div style="margin: 3rem 0 2rem 0;"></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    create_info_card(
        "🎯",
        "How to Get Started",
        "Navigate through the sidebar to explore different data insights. Start with Car Ownership to understand vehicle trends.",
        "#667eea 0%, #764ba2 100%"
    )

with col2:
    create_info_card(
        "📊",
        "Data Sources",
        "This application uses data from Melbourne Open Data Platform, Australian Bureau of Statistics, and real-time parking sensor networks.",
        "#11998e 0%, #38ef7d 100%"
    )

# 页脚
create_footer()