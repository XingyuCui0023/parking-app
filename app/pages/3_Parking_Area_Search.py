# app/pages/3_Parking_Area_Search.py
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium

# ---------- 1) 连接数据库 ----------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="Parking Area Search", layout="wide")
st.title("Parking Area Search")
st.caption("Tip: Use a radius to define a smaller area first and then gradually expand it for faster loading.")

# ---------- 2) 侧栏参数 ----------
default_lat = -37.8136
default_lon = 144.9631
with st.sidebar:
    st.header("Filter")
    lat = st.number_input("Latitude", value=default_lat, format="%.6f")
    lon = st.number_input("Longitude", value=default_lon, format="%.6f")
    radius_m = st.slider("Radius (meters)", min_value=100, max_value=3000, value=600, step=100)
    limit = st.slider("Max points", min_value=200, max_value=5000, value=2000, step=200)

# ---------- 3) 查询范围内点位 + 最新状态 ----------
sql = text("SELECT * FROM get_bays_within(:lon, :lat, :radius, :limit)")
with engine.begin() as conn:
    df = pd.read_sql(sql, conn, params={"lon": lon, "lat": lat, "radius": radius_m, "limit": limit})

# ✅ 只看空位开关（放在查询后、渲染前）
show_free_only = st.sidebar.checkbox("Only show free bays", value=False)
if show_free_only:
    df = df[df["is_occupied"] == False]

st.write(f"Loaded {len(df)} bays.")
if df.empty:
    st.info("There are no points within the range. Try increasing the radius or changing the center point.")

# ---------- 4) 顶部小指标 ----------
if not df.empty:
    total = len(df)
    free_cnt = int((df["is_occupied"] == False).sum())
    occ_cnt = int((df["is_occupied"] == True).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Total bays in radius", total)
    c2.metric("Free (green)", free_cnt)
    c3.metric("Occupied (red)", occ_cnt)

# ---------- 5) 地图渲染（含一键导航） ----------
m = folium.Map(location=[lat, lon], zoom_start=16, tiles="cartodbpositron")

# 中心点 + 圆
folium.CircleMarker(
    location=[lat, lon], radius=6, color="#1f77b4", fill=True, fill_opacity=0.9, popup="Center"
).add_to(m)
folium.Circle(location=[lat, lon], radius=radius_m, color="#1f77b4", fill=False).add_to(m)

# 点 + 导航链接
for _, r in df.iterrows():
    color = "red" if r["is_occupied"] else "green"
    status = "Occupied" if r["is_occupied"] else "Unoccupied"
    gmaps = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={r['lat']},{r['lon']}"
        f"&travelmode=driving"
    )
    popup_html = folium.IFrame(
        html=f"""
        <div style="font-size:14px; line-height:1.4;">
          <b>Bay ID:</b> {int(r['bay_id'])}<br/>
          <b>Status:</b> {status}<br/>
          <b>Updated:</b> {r['status_timestamp']}<br/>
          <a href="{gmaps}" target="_blank">🧭 Open in Google Maps</a>
        </div>
        """,
        width=260, height=120
    )
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)

st_map = st_folium(m, width=1200, height=700)

# ---------- 6) 可选：查看单个 bay 的历史 ----------
st.subheader("Bay history (optional)")
if not df.empty:
    col1, col2 = st.columns([2, 1])
    with col1:
        bay_id = st.selectbox(
            "Pick a bay to view history",
            options=df["bay_id"].astype(int).unique(),
            format_func=lambda x: f"bay {x}",
        )
    with col2:
        hours = st.slider("Lookback hours", 6, 72, 48, step=6)

    if bay_id:
        hist_sql = text("SELECT * FROM get_bay_history(:bay_id, :hrs)")
        with engine.begin() as conn:
            hist = pd.read_sql(hist_sql, conn, params={"bay_id": int(bay_id), "hrs": int(hours)})

        if hist.empty:
            st.info("No history for this bay in the selected period.")
        else:
            st.dataframe(hist, use_container_width=True, hide_index=True)

            # 占用=1 / 空闲=0 折线
            chart_df = hist[["status_timestamp", "is_occupied"]].copy()
            chart_df["occupied"] = chart_df["is_occupied"].astype(int)
            chart_df = chart_df.set_index("status_timestamp")[["occupied"]]
            st.line_chart(chart_df)
