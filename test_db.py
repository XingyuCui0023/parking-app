from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# 加载 .env
load_dotenv()

url = os.getenv("DATABASE_URL")
print("URL ok:", bool(url))

# 连接数据库
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("Database version:", result.fetchone())
