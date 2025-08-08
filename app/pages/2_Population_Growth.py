# app/pages/2_Population_Growth.py
import os
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

st.title("Population Growth in Victoria (2001–2021)")
st.caption("Drag the range to focus on specific years.")

@st.cache_data(ttl=600)
def fetch_population():
    sql = text("SELECT * FROM population_cbd ORDER BY year")
    with engine.begin() as conn:
        return pd.read_sql(sql, conn)

df = fetch_population()

if df.empty:
    st.info("No population data found.")
else:
    min_y, max_y = int(df["year"].min()), int(df["year"].max())
    start_year, end_year = st.slider(
        "Select year range", min_y, max_y, (2001, 2021), step=1
    )

    df_filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)]

    line = (
        alt.Chart(df_filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("residents:Q", title="Residents"),
            tooltip=["year", "residents"]
        )
        .properties(height=420)
    )
    st.altair_chart(line, use_container_width=True)

    # 小指标
    st.metric(
        label="CAGR (selected range)",
        value=f"{((df_filtered['residents'].iloc[-1] / df_filtered['residents'].iloc[0]) ** (1 / (end_year - start_year)) - 1):.2%}"
        if len(df_filtered) > 1 else "—"
    )
