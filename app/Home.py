import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Home", layout="wide")

# 找到图片路径
CURRENT_DIR = Path(__file__).parent
IMAGE_PATH = CURRENT_DIR / "assets" / "home.png"

# 读取并显示
if IMAGE_PATH.exists():
    st.image(str(IMAGE_PATH), use_container_width=True)
else:
    st.error(f"Image not found: {IMAGE_PATH}")
