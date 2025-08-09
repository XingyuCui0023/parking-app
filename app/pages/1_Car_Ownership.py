# app/pages/1_Car_Ownership.py
import os
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from lib.db import get_engine
from lib.ui_components import (
    apply_safe_custom_css, create_header, create_info_box, 
    create_footer, create_metric_card
)

# 页面配置
st.set_page_config(
    page_title="Car Ownership Analysis", 
    page_icon="🚗",
    layout="wide"
)

# 应用安全的自定义样式
apply_safe_custom_css()

# 页面标题
create_header(
    "Car Ownership Analysis", 
    "Compare Victoria with other Australian states (2016–2020)"
)

# 数据库连接
try:
    engine = get_engine()
    db_available = True
except Exception as e:
    st.warning("⚠️ **Database unavailable, running in Demo Mode** - " + str(e)[:100] + "...")
    db_available = False

# 演示数据
demo_data = {
    'states': ['Vic.', 'NSW', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT'],
    'car_ownership': pd.DataFrame({
        'year': [2016, 2017, 2018, 2019, 2020] * 8,
        'state': ['Vic.'] * 5 + ['NSW'] * 5 + ['QLD'] * 5 + ['SA'] * 5 + ['WA'] * 5 + ['TAS'] * 5 + ['NT'] * 5 + ['ACT'] * 5,
        'number': [
            # Vic.
            320000, 325000, 330000, 315000, 295000,
            # NSW
            420000, 425000, 430000, 415000, 385000,
            # QLD
            280000, 285000, 290000, 275000, 255000,
            # SA
            120000, 125000, 130000, 125000, 115000,
            # WA
            180000, 185000, 190000, 185000, 170000,
            # TAS
            35000, 36000, 37000, 36000, 33000,
            # NT
            25000, 26000, 27000, 26000, 24000,
            # ACT
            28000, 29000, 30000, 29000, 27000
        ]
    })
}

@st.cache_data(ttl=600)
def fetch_states():
    if db_available:
        sql = text("SELECT DISTINCT state FROM car_ownership_by_state ORDER BY state")
        with engine.begin() as conn:
            return pd.read_sql(sql, conn)["state"].tolist()
    else:
        return demo_data['states']

@st.cache_data(ttl=600)
def fetch_car_ownership(vic_label: str, other: str | None):
    if db_available:
        if other is None:
            sql = text("""
                SELECT year, number, state
                FROM car_ownership_by_state
                WHERE state = :vic
                ORDER BY year
            """)
            params = {"vic": vic_label}
        else:
            sql = text("""
                SELECT year, number, state
                FROM car_ownership_by_state
                WHERE state IN (:vic, :other)
                ORDER BY year
            """)
            params = {"vic": vic_label, "other": other}
        with engine.begin() as conn:
            return pd.read_sql(sql, conn, params=params)
    else:
        # 使用演示数据
        df = demo_data['car_ownership'].copy()
        if other is None:
            return df[df['state'] == vic_label]
        else:
            return df[df['state'].isin([vic_label, other])]

# 美化侧边栏


# 州列表 & 找到真实的 Vic 写法（可能是 'Vic.'、'VIC' 等）
all_states = fetch_states()
vic_label = next((s for s in all_states if s.lower().startswith("vic")), "Vic.")

# 控制面板
with st.sidebar:
    st.markdown("### Analysis Settings")
    
    # 选择对比州（去掉 VIC）
    compare_options = [s for s in all_states if s != vic_label]
    selected_state = st.selectbox(
        "Select state for comparison",
        options=[None] + compare_options,
        format_func=lambda x: "None (VIC only)" if x is None else x,
        help="Choose another state to compare with Victoria"
    )
    
    # 显示选择信息
    if selected_state:
        st.success(f"Comparing {vic_label} vs {selected_state}")
    else:
        st.info(f"Showing {vic_label} only")

df = fetch_car_ownership(vic_label, selected_state)

# 主要内容区域
if df.empty:
    st.error("No data found. Please check your database connection.")
else:
    # 数据概览
    col1, col2, col3, col4 = st.columns(4)
    
    # 计算统计指标
    vic_data = df[df['state'] == vic_label] if not df.empty else pd.DataFrame()
    total_vic = vic_data['number'].sum() if not vic_data.empty else 0
    avg_vic = vic_data['number'].mean() if not vic_data.empty else 0
    
    if selected_state:
        other_data = df[df['state'] == selected_state]
        total_other = other_data['number'].sum() if not other_data.empty else 0
        comparison = f"+{((total_vic/total_other-1)*100):.1f}%" if total_other > 0 else "N/A"
    else:
        comparison = None
    
    with col1:
        st.markdown(create_metric_card(
            f"{vic_label} Total", 
            f"{total_vic:,.0f}", 
            "2016-2020"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            f"{vic_label} Average", 
            f"{avg_vic:,.0f}", 
            "Per Year"
        ), unsafe_allow_html=True)
    
    with col3:
        if selected_state and not df[df['state'] == selected_state].empty:
            other_total = df[df['state'] == selected_state]['number'].sum()
            st.markdown(create_metric_card(
                f"{selected_state} Total", 
                f"{other_total:,.0f}", 
                "2016-2020"
            ), unsafe_allow_html=True)
        else:
            st.markdown(create_metric_card(
                "States Available", 
                f"{len(all_states)}", 
                "Total"
            ), unsafe_allow_html=True)
    
    with col4:
        if comparison and comparison != "N/A":
            st.markdown(create_metric_card(
                "VIC vs Selected", 
                comparison, 
                "Difference"
            ), unsafe_allow_html=True)
        else:
            years_span = df['year'].max() - df['year'].min() + 1
            st.markdown(create_metric_card(
                "Years Covered", 
                f"{years_span}", 
                "2016-2020"
            ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 图表容器
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # 改进的图表
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("number:Q", title="New Vehicle Registrations", axis=alt.Axis(format=",.0f")),
            color=alt.Color(
                "state:N", 
                title="State",
                scale=alt.Scale(range=['#3b82f6', '#ef4444', '#10b981', '#f59e0b'])
            ),
            tooltip=[
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("number:Q", title="Registrations", format=",.0f")
            ]
        )
        .properties(
            height=450,
            title=alt.TitleParams(
                text="Vehicle Registration Trends by State",
                fontSize=16,
                fontWeight="bold",
                anchor="start"
            )
        )
        .resolve_scale(color='independent')
    )
    
    st.altair_chart(chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 数据洞察
    if selected_state:
        create_info_box(
            "Key Insights",
            f"Victoria shows {'higher' if comparison and '+' in comparison else 'different'} vehicle registration numbers compared to {selected_state}. "
            f"This data reflects economic conditions, population growth, and transportation preferences across Australian states.",
            "💡"
        )
    else:
        create_info_box(
            "About This Data",
            f"Victoria registered an average of {avg_vic:,.0f} new vehicles per year between 2016-2020. "
            "Select another state from the sidebar to see comparative analysis.",
            "📈"
        )

# 页脚
create_footer()
