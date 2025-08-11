# app/pages/3_Parking_Area_Search.py
import os
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium

# ---------- 1) 连接数据库 ----------
from lib.db import get_engine
from lib.ui_components import (
    apply_safe_custom_css, create_header, create_info_box, 
    create_footer, create_metric_card, create_status_badge
)

# 页面配置
st.set_page_config(
    page_title="Smart Parking Search", 
    page_icon="🅿️",
    layout="wide"
)

# 应用安全的自定义样式
apply_safe_custom_css()

# 页面标题
create_header(
    "Smart Parking Search", 
    "Find available parking spots in Melbourne CBD with real-time data"
)

# 数据库连接
try:
    engine = get_engine()
    db_available = True
except Exception as e:
    st.warning("⚠️ **Database unavailable, running in Demo Mode** - " + str(e)[:100] + "...")
    db_available = False

# 演示停车数据
import numpy as np
import datetime as dt

def generate_demo_parking_data(lat, lon, radius_m, limit):
    """生成演示停车数据"""
    np.random.seed(42)  # 固定随机种子以获得一致的结果
    
    # 根据半径生成停车位数量
    num_bays = min(limit, max(50, int(radius_m / 10)))
    
    # 生成随机位置（在指定半径内）
    angles = np.random.uniform(0, 2*np.pi, num_bays)
    distances = np.random.uniform(0, radius_m, num_bays)
    
    # 转换为经纬度偏移 (大概的转换)
    lat_offset = distances * np.cos(angles) / 111000  # 大约111km每度
    lon_offset = distances * np.sin(angles) / (111000 * np.cos(np.radians(lat)))
    
    demo_data = []
    for i in range(num_bays):
        demo_data.append({
            'bay_id': 1000 + i,
            'lat': lat + lat_offset[i],
            'lon': lon + lon_offset[i],
            'is_occupied': np.random.choice([True, False], p=[0.3, 0.7]),  # 30%占用率
            'status_timestamp': dt.datetime.now() - dt.timedelta(minutes=np.random.randint(1, 120))
        })
    
    return pd.DataFrame(demo_data)

# ---------- 2) 美化侧栏参数 ----------


default_lat = -37.8136
default_lon = 144.9631

with st.sidebar:
    st.markdown("### Search Settings")
    
    # 预设位置
    preset_locations = {
        "Melbourne CBD": (-37.8136, 144.9631),
        "Federation Square": (-37.8179, 144.9690),
        "Queen Victoria Market": (-37.8076, 144.9568),
        "Southern Cross Station": (-37.8183, 144.9527),
        "Custom Location": None
    }
    
    location_choice = st.selectbox(
        "📍 Choose location",
        options=list(preset_locations.keys()),
        help="Select a preset location or choose Custom to enter coordinates"
    )
    
    if location_choice == "Custom Location":
        lat = st.number_input("🌐 Latitude", value=default_lat, format="%.6f")
        lon = st.number_input("🌐 Longitude", value=default_lon, format="%.6f")
    else:
        lat, lon = preset_locations[location_choice]
        st.success(f"📍 Location: {location_choice}")
    
    st.markdown("---")
    
    # 搜索参数
    st.markdown("### 🔍 Search Parameters")
    radius_m = st.slider(
        "🎯 Search radius (meters)", 
        min_value=100, 
        max_value=3000, 
        value=600, 
        step=100,
        help="Larger radius = more results but slower loading"
    )
    
    limit = st.slider(
        "📊 Maximum results", 
        min_value=200, 
        max_value=5000, 
        value=2000, 
        step=200,
        help="Limit results for better performance"
    )

# ---------- 3) 查询数据并添加过滤选项 ----------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🎛️ Display Options")
    
    show_free_only = st.checkbox("🟢 Only show available bays", value=False)
    show_occupied_only = st.checkbox("🔴 Only show occupied bays", value=False)
    
    if show_free_only and show_occupied_only:
        st.warning("⚠️ Both filters selected - showing all bays")

# 获取数据
with st.spinner("🔍 Searching for parking bays..."):
    if db_available:
        sql = text("SELECT * FROM get_bays_within(:lon, :lat, :radius, :limit)")
        with engine.begin() as conn:
            df = pd.read_sql(sql, conn, params={"lon": lon, "lat": lat, "radius": radius_m, "limit": limit})
    else:
        # 使用演示数据
        df = generate_demo_parking_data(lat, lon, radius_m, limit)

# 应用过滤器
original_count = len(df)
if show_free_only and not show_occupied_only:
    df = df[df["is_occupied"] == False]
elif show_occupied_only and not show_free_only:
    df = df[df["is_occupied"] == True]

# 状态消息
if df.empty:
    create_info_box(
        "No Results Found",
        f"No parking bays found within {radius_m}m of the selected location. Try increasing the search radius or selecting a different location.",
        "⚠️"
    )
else:
    if len(df) < original_count:
        st.info(f"🔍 Showing {len(df)} filtered results out of {original_count} total bays")
    else:
        st.success(f"✅ Found {len(df)} parking bays in the search area")

# ---------- 4) 美化的指标卡片 ----------
if not df.empty:
    total = len(df)
    free_cnt = int((df["is_occupied"] == False).sum())
    occ_cnt = int((df["is_occupied"] == True).sum())
    availability_rate = (free_cnt / total * 100) if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Bays", 
            f"{total:,}", 
            f"Within {radius_m}m"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Available", 
            f"{free_cnt:,}", 
            f"{availability_rate:.1f}% free"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Occupied", 
            f"{occ_cnt:,}", 
            f"{100-availability_rate:.1f}% full"
        ), unsafe_allow_html=True)
    
    with col4:
        status_color = "🟢" if availability_rate > 30 else "🟡" if availability_rate > 10 else "🔴"
        status_text = "Good" if availability_rate > 30 else "Limited" if availability_rate > 10 else "Poor"
        st.markdown(create_metric_card(
            "Availability", 
            f"{status_color} {status_text}", 
            f"{availability_rate:.1f}%"
        ), unsafe_allow_html=True)

# ---------- 5) 改进的地图渲染 ----------
if not df.empty:
    st.markdown("---")
    st.markdown("### 🗺️ Interactive Parking Map")
    
    # 地图样式选择
    col_map1, col_map2 = st.columns([3, 1])
    
    with col_map2:
        map_style = st.selectbox(
            "🎨 Map Style",
            options=["cartodbpositron", "OpenStreetMap", "cartodbdark_matter"],
            format_func=lambda x: {
                "cartodbpositron": "Light",
                "OpenStreetMap": "Standard", 
                "cartodbdark_matter": "Dark"
            }[x]
        )
    
    with col_map1:
        st.markdown(f"📍 **Location**: {location_choice} | **Radius**: {radius_m}m | **Results**: {len(df)} bays")
    
    # 创建地图
    m = folium.Map(
        location=[lat, lon], 
        zoom_start=16, 
        tiles=map_style,
        prefer_canvas=True
    )
    
    # 中心点标记 - 更美观的样式
    folium.Marker(
        location=[lat, lon],
        popup=f"<b>Search Center</b><br/>{location_choice}",
        icon=folium.Icon(color="blue", icon="bullseye", prefix="fa"),
        tooltip="Search Center"
    ).add_to(m)
    
    # 搜索半径圆圈
    folium.Circle(
        location=[lat, lon], 
        radius=radius_m, 
        color="#3b82f6", 
        fill=False,
        weight=2,
        opacity=0.8,
        popup=f"Search Radius: {radius_m}m"
    ).add_to(m)
    
    # 添加停车位标记
    for _, r in df.iterrows():
        color = "#ef4444" if r["is_occupied"] else "#10b981"  # 红色/绿色
        icon_color = "red" if r["is_occupied"] else "green"
        status = "Occupied" if r["is_occupied"] else "Available"
        icon_symbol = "car" if r["is_occupied"] else "check"
        
        # Google Maps导航链接
        gmaps_url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&destination={r['lat']},{r['lon']}"
            f"&travelmode=driving"
        )
        
        # 美化的弹窗内容
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 250px;">
            <div style="background: {'#fef2f2' if r['is_occupied'] else '#f0fdf4'}; 
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;
                        border-left: 4px solid {color};">
                <h4 style="margin: 0 0 8px 0; color: #1f2937;">
                    🅿️ Bay #{int(r['bay_id'])}
                </h4>
                <p style="margin: 4px 0; color: #374151;">
                    <b>Status:</b> 
                    <span style="color: {color}; font-weight: bold;">
                        {'🔴' if r['is_occupied'] else '🟢'} {status}
                    </span>
                </p>
                <p style="margin: 4px 0; color: #6b7280; font-size: 0.9em;">
                    <b>Last Updated:</b><br/>{r['status_timestamp']}
                </p>
            </div>
            <div style="text-align: center;">
                <a href="{gmaps_url}" target="_blank" 
                   style="display: inline-block; background: #3b82f6; color: white; 
                          padding: 8px 16px; text-decoration: none; border-radius: 6px;
                          font-weight: bold;">
                    🧭 Navigate Here
                </a>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=6,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Bay #{int(r['bay_id'])} - {status}"
        ).add_to(m)
    
    # 添加图例
    legend_html = f"""
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 120px; 
                background-color: white; border: 2px solid grey; z-index:9999; 
                font-size: 14px; border-radius: 8px; padding: 10px;">
    <h4 style="margin-top: 0;">Legend</h4>
    <p><span style="color: #10b981;">🟢</span> Available ({free_cnt} bays)</p>
    <p><span style="color: #ef4444;">🔴</span> Occupied ({occ_cnt} bays)</p>
    <p><span style="color: #3b82f6;">📍</span> Search Center</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 显示地图
    st_map = st_folium(m, width=1200, height=700, returned_objects=["last_object_clicked"])

# ---------- 6) 改进的历史数据分析 ----------
if not df.empty:
    st.markdown("---")
    st.markdown("### 📊 Bay History Analysis")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        bay_id = st.selectbox(
            "🎯 Select bay for detailed analysis",
            options=sorted(df["bay_id"].astype(int).unique()),
            format_func=lambda x: f"🅿️ Bay #{x}",
            help="Choose a parking bay to view its historical occupancy patterns"
        )
    
    with col2:
        hours = st.slider(
            "📅 Lookback period", 
            min_value=6, 
            max_value=168, 
            value=48, 
            step=6,
            help="Hours of historical data to analyze"
        )
    
    with col3:
        if st.button(" Refresh Data ", type="primary"):
            st.rerun()

    if bay_id:
        with st.spinner(f"📈 Loading history for Bay #{bay_id}..."):
            if db_available:
                hist_sql = text("SELECT * FROM get_bay_history(:bay_id, :hrs)")
                with engine.begin() as conn:
                    hist = pd.read_sql(hist_sql, conn, params={"bay_id": int(bay_id), "hrs": int(hours)})
            else:
                # 生成演示历史数据
                np.random.seed(int(bay_id))
                num_records = min(50, max(5, int(hours / 2)))
                hist_data = []
                current_time = dt.datetime.now()
                
                for i in range(num_records):
                    hist_data.append({
                        'bay_id': bay_id,
                        'is_occupied': np.random.choice([True, False], p=[0.4, 0.6]),
                        'status_timestamp': current_time - dt.timedelta(hours=hours * i / num_records)
                    })
                
                hist = pd.DataFrame(hist_data).sort_values('status_timestamp')

        if hist.empty:
            create_info_box(
                "No Historical Data",
                f"No historical data found for Bay #{bay_id} in the last {hours} hours. This could mean the bay is new or has no recorded status changes.",
                "ℹ️"
            )
        else:
            # 历史数据统计
            total_records = len(hist)
            occupied_records = hist["is_occupied"].sum()
            occupancy_rate = (occupied_records / total_records * 100) if total_records > 0 else 0
            
            # 统计卡片
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(create_metric_card(
                    "Total Records", 
                    f"{total_records:,}", 
                    f"Last {hours}h"
                ), unsafe_allow_html=True)
            
            with col2:
                st.markdown(create_metric_card(
                    "Occupied Time", 
                    f"{occupancy_rate:.1f}%", 
                    f"{occupied_records} records"
                ), unsafe_allow_html=True)
            
            with col3:
                st.markdown(create_metric_card(
                    "Available Time", 
                    f"{100-occupancy_rate:.1f}%", 
                    f"{total_records-occupied_records} records"
                ), unsafe_allow_html=True)
            
            with col4:
                pattern = "High Turnover" if total_records > 20 else "Stable" if total_records > 5 else "Low Activity"
                st.markdown(create_metric_card(
                    "Activity Level", 
                    pattern, 
                    f"{total_records} changes"
                ), unsafe_allow_html=True)
            
            # 数据表格
            st.markdown("#### 📋 Historical Records")
            
            # 格式化数据表格 - 确保列名一致性
            hist_display = hist.copy()
            
            # 添加状态显示列
            if 'is_occupied' in hist_display.columns:
                hist_display['status_display'] = hist_display['is_occupied'].apply(
                    lambda x: "🔴 Occupied" if x else "🟢 Available"
                )
            elif 'occupied' in hist_display.columns:
                hist_display['status_display'] = hist_display['occupied'].apply(
                    lambda x: "🔴 Occupied" if x else "🟢 Available"
                )
            
            # 重命名列 - 使用安全的列名映射
            column_mapping = {}
            if 'status_timestamp' in hist_display.columns:
                column_mapping['status_timestamp'] = 'Timestamp'
            elif 'timestamp' in hist_display.columns:
                column_mapping['timestamp'] = 'Timestamp'
            
            if 'bay_id' in hist_display.columns:
                column_mapping['bay_id'] = 'Bay ID'
            elif 'bayid' in hist_display.columns:
                column_mapping['bayid'] = 'Bay ID'
            
            if column_mapping:
                hist_display = hist_display.rename(columns=column_mapping)
            
            # 确保所需的列存在
            display_columns = []
            if 'Timestamp' in hist_display.columns:
                display_columns.append('Timestamp')
            if 'status_display' in hist_display.columns:
                display_columns.append('status_display')
                # 重命名status_display为Status
                hist_display = hist_display.rename(columns={'status_display': 'Status'})
                display_columns[-1] = 'Status'
            if 'Bay ID' in hist_display.columns:
                display_columns.append('Bay ID')
            
            # 如果所有必需的列都存在，显示数据表格
            if len(display_columns) >= 2:  # 至少需要时间戳和状态
                st.dataframe(
                    hist_display[display_columns], 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning("Historical data format is not compatible with display. Showing raw data.")
                st.dataframe(hist_display, use_container_width=True, hide_index=True)
            
            # 可视化图表
            st.markdown("#### 📈 Occupancy Timeline")
            
            # 准备图表数据 - 确保列名一致性
            chart_df = hist.copy()
            
            # 确定时间戳列名
            time_col = None
            if 'status_timestamp' in chart_df.columns:
                time_col = 'status_timestamp'
            elif 'timestamp' in chart_df.columns:
                time_col = 'timestamp'
            
            # 确定占用状态列名
            occupied_col = None
            if 'is_occupied' in chart_df.columns:
                occupied_col = 'is_occupied'
            elif 'occupied' in chart_df.columns:
                occupied_col = 'occupied'
            
            if time_col and occupied_col:
                chart_df = chart_df[[time_col, occupied_col]].copy()
                chart_df["occupied"] = chart_df[occupied_col].astype(int)
                chart_df = chart_df.rename(columns={time_col: 'status_timestamp'})
            else:
                st.warning("Cannot create chart: missing required columns for visualization.")
                chart_df = pd.DataFrame()
            
            # 使用Altair创建更美观的图表
            if not chart_df.empty:
                chart = alt.Chart(chart_df).mark_line(
                    point=True,
                    strokeWidth=3,
                    color='#3b82f6'
                ).encode(
                    x=alt.X('status_timestamp:T', title='Time', axis=alt.Axis(format='%m/%d %H:%M')),
                    y=alt.Y('occupied:Q', title='Occupancy Status', scale=alt.Scale(domain=[0, 1])),
                    tooltip=[
                        alt.Tooltip('status_timestamp:T', title='Time'),
                        alt.Tooltip('occupied:Q', title='Occupied (1=Yes, 0=No)')
                    ]
                ).properties(
                    height=300,
                    title=f"Bay #{bay_id} Occupancy Pattern (Last {hours} hours)"
                )
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No chart data available for this bay.")
            
            # 分析洞察
            if occupancy_rate > 80:
                insight = f"This bay is heavily utilized ({occupancy_rate:.1f}% occupied). Consider this as a backup option."
            elif occupancy_rate > 50:
                insight = f"This bay has moderate usage ({occupancy_rate:.1f}% occupied). Good chance of finding it available."
            else:
                insight = f"This bay is frequently available ({100-occupancy_rate:.1f}% free). High probability of finding parking here."
            
            create_info_box(
                "Usage Insights",
                insight + f" Based on {total_records} status changes in the last {hours} hours.",
                "💡"
            )

# 使用提示
create_info_box(
    "Pro Tips",
    "• Use the preset locations for quick searches of popular areas\n"
    "• Start with a smaller radius (300-600m) for faster loading\n"
    "• Check the availability percentage to gauge your chances\n"
    "• Click on any bay marker to get navigation directions",
    "💡"
)

# 页脚
create_footer()
