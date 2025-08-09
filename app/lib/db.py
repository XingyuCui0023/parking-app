# app/lib/db.py
import os
from pathlib import Path
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

def _build_db_url() -> str:
    """
    读取 DB URL 的优先级：
    1) Streamlit secrets（Cloud 或本地 secrets.toml）
    2) 项目根目录的 .env（显式加载）
    3) 环境变量（兜底）
    并统一追加 sslmode=require；兼容 postgres:// 前缀。
    如果没有找到数据库URL，返回None以启用演示模式。
    """
    # 1) 试图从 secrets 读取（本地没有 secrets.toml 时会抛异常，所以 try）
    url = None
    try:
        url = st.secrets.get("DATABASE_URL")
    except Exception:
        url = None

    # 2) 如果没有，从项目根 .env 读取
    if not url:
        # db.py 位于 app/lib/db.py -> 项目根是上上级目录
        project_root = Path(__file__).resolve().parents[2]
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
        url = os.getenv("DATABASE_URL")

    # 3) 兜底：环境变量（即使没加载 .env）
    if not url:
        url = os.getenv("DATABASE_URL")

    # 如果仍然没有URL，返回None以启用演示模式
    if not url or url.strip() == "":
        return None

    # 兼容 postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # 统一追加 SSL
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"

    return url

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        db_url = _build_db_url()
        if db_url is None:
            raise RuntimeError("No database URL configured - running in demo mode")
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine
