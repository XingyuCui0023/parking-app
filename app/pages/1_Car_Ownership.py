# app/pages/1_Car_Ownership.py
import os
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

st.title("Car Ownership by State (2016–2020)")
st.caption("Compare Victoria with another state.")

@st.cache_data(ttl=600)
def fetch_states():
    sql = text("SELECT DISTINCT state FROM car_ownership_by_state ORDER BY state")
    with engine.begin() as conn:
        return pd.read_sql(sql, conn)["state"].tolist()

@st.cache_data(ttl=600)
def fetch_car_ownership(vic_label: str, other: str | None):
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

# 州列表 & 找到真实的 Vic 写法（可能是 'Vic.'、'VIC' 等）
all_states = fetch_states()
vic_label = next((s for s in all_states if s.lower().startswith("vic")), "Vic.")

# 选择对比州（去掉 VIC）
compare_options = [s for s in all_states if s != vic_label]
selected_state = st.selectbox(
    "Select another state for comparison",
    options=[None] + compare_options,
    format_func=lambda x: "None (VIC only)" if x is None else x,
)

df = fetch_car_ownership(vic_label, selected_state)

# 可视化
if df.empty:
    st.info("No data found.")
else:
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("number:Q", title="New registrations"),
            color=alt.Color("state:N", title="State"),
            tooltip=["state", "year", "number"]
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)
