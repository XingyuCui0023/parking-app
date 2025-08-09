# app/pages/2_Population_Growth.py
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
    page_title="Population Growth Analysis", 
    page_icon="📈",
    layout="wide"
)

# 应用安全的自定义样式
apply_safe_custom_css()

# 页面标题
create_header(
    "Population Growth Analysis", 
    "Victoria's demographic trends and urban development (2001–2021)"
)

# 数据库连接
try:
    engine = get_engine()
    db_available = True
except Exception as e:
    st.warning("⚠️ **Database unavailable, running in Demo Mode** - " + str(e)[:100] + "...")
    db_available = False

# 演示数据
demo_population_data = pd.DataFrame({
    'year': list(range(2001, 2022)),
    'residents': [
        3850000, 3900000, 3950000, 4000000, 4050000,  # 2001-2005
        4100000, 4150000, 4200000, 4250000, 4300000,  # 2006-2010
        4350000, 4400000, 4450000, 4500000, 4550000,  # 2011-2015
        4600000, 4650000, 4700000, 4750000, 4800000,  # 2016-2020
        4850000  # 2021
    ]
})

@st.cache_data(ttl=600)
def fetch_population():
    if db_available:
        sql = text("SELECT * FROM population_cbd ORDER BY year")
        with engine.begin() as conn:
            return pd.read_sql(sql, conn)
    else:
        return demo_population_data

# 美化侧边栏


df = fetch_population()

if df.empty:
    st.error("No population data found. Please check your database connection.")
else:
    min_y, max_y = int(df["year"].min()), int(df["year"].max())
    
    # 控制面板
    with st.sidebar:
        st.markdown("### Analysis Controls")
        
        start_year, end_year = st.slider(
            "Select year range",
            min_value=min_y, 
            max_value=max_y, 
            value=(2001, 2021), 
            step=1,
            help="Drag to focus on specific time periods"
        )
        
        # 显示选择信息
        st.info(f"Analyzing {end_year - start_year + 1} years of data")
        
        # 分析选项
        show_trend = st.checkbox("📈 Show trend line", value=True)
        show_points = st.checkbox("⚫ Show data points", value=True)

    df_filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    
    if len(df_filtered) < 2:
        st.warning("⚠️ Please select at least 2 years for meaningful analysis.")
    else:
        # 计算关键指标
        start_pop = df_filtered['residents'].iloc[0]
        end_pop = df_filtered['residents'].iloc[-1]
        total_growth = end_pop - start_pop
        growth_rate = ((end_pop / start_pop) ** (1 / (end_year - start_year)) - 1) if end_year != start_year else 0
        avg_pop = df_filtered['residents'].mean()
        
        # 指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Starting Population", 
                f"{start_pop:,.0f}", 
                f"Year {start_year}"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Ending Population", 
                f"{end_pop:,.0f}", 
                f"Year {end_year}"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Total Growth", 
                f"{total_growth:+,.0f}", 
                f"{((end_pop/start_pop-1)*100):+.1f}%"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "CAGR", 
                f"{growth_rate:.2%}", 
                "Annual Growth"
            ), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 图表容器
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # 创建基础图表
        base = alt.Chart(df_filtered).add_params(
            alt.selection_interval(bind='scales')
        )
        
        # 线图
        line = base.mark_line(
            point=show_points,
            strokeWidth=3,
            color='#3b82f6'
        ).encode(
            x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("residents:Q", title="Population", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("residents:Q", title="Population", format=",.0f")
            ]
        )
        
        # 趋势线
        if show_trend and len(df_filtered) > 2:
            trend = base.transform_regression('year', 'residents').mark_line(
                strokeDash=[5, 5],
                color='#ef4444',
                strokeWidth=2
            ).encode(
                x='year:O',
                y='residents:Q'
            )
            chart = line + trend
        else:
            chart = line
        
        # 图表属性
        chart = chart.properties(
            height=450,
            title=alt.TitleParams(
                text=f"Victoria Population Trends ({start_year}-{end_year})",
                fontSize=16,
                fontWeight="bold",
                anchor="start"
            )
        ).resolve_scale(
            y='independent'
        )
        
        st.altair_chart(chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 数据洞察
        if growth_rate > 0:
            growth_desc = "growing"
            growth_impact = "This positive growth indicates urban development, economic opportunities, and increased demand for infrastructure and services."
        elif growth_rate < 0:
            growth_desc = "declining"
            growth_impact = "This decline may reflect urban planning changes, economic shifts, or demographic transitions."
        else:
            growth_desc = "stable"
            growth_impact = "This stability suggests a mature urban environment with balanced in and out migration."
        
        create_info_box(
            "Population Insights",
            f"Victoria's population is {growth_desc} at an average rate of {growth_rate:.2%} per year over the selected period. "
            f"{growth_impact} The total change of {total_growth:+,.0f} residents represents significant urban dynamics.",
            "🏙️"
        )
        
        # 年度变化分析
        if len(df_filtered) > 1:
            df_changes = df_filtered.copy()
            df_changes['yearly_change'] = df_changes['residents'].diff()
            df_changes['yearly_change_pct'] = df_changes['residents'].pct_change() * 100
            
            # 找出最大增长年份
            if not df_changes['yearly_change'].isna().all():
                max_growth_year = df_changes.loc[df_changes['yearly_change'].idxmax(), 'year']
                max_growth = df_changes['yearly_change'].max()
                
                create_info_box(
                    "Peak Growth Year",
                    f"The largest population increase occurred in {max_growth_year} with {max_growth:+,.0f} new residents. "
                    "This could indicate significant urban development, policy changes, or economic factors during that period.",
                    "📊"
                )

# 页脚
create_footer()
