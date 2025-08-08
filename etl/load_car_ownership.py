import os, re
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
ENGINE = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)

XLSX  = Path("app/data/car_ownership.xlsx")
SHEET = 0  # 如需指定工作表名改这里

# 列索引（从0开始）：B=1,D=3,F=5,H=7,J=9；百分比列 C=2,E=4,G=6,I=8,K=10
YEAR_MAP = {2016:(1,2), 2017:(3,4), 2018:(5,6), 2019:(7,8), 2020:(9,10)}

STATES = {"nsw","vic.","qld","sa","wa","tas.","nt","act","aust."}

def to_int(s):
  if pd.isna(s): return None
  return int(re.sub(r"[,\s]","", str(s)))

def load_all_states():
  raw = pd.read_excel(XLSX, sheet_name=SHEET, header=None, engine="openpyxl")

  # 找到州名所在的行（第一列）
  rows = []
  for i in range(raw.shape[0]):
    label = str(raw.iat[i,0]).strip()
    if label and label.lower() in STATES:  # 匹配 NSW / Vic. 等
      rows.append(i)

  if not rows:
    raise RuntimeError("没找到州名行，请确认第一列是 NSW/Vic./Qld...")

  data = []
  for r in rows:
    state = str(raw.iat[r,0]).strip()   # 维持原写法，如 'Vic.'
    for y,(col_no,col_pct) in YEAR_MAP.items():
      num = to_int(raw.iat[r, col_no])
      pct = raw.iat[r, col_pct]
      if num is not None:
        data.append({"state": state, "year": y, "number": num, "pct": None if pd.isna(pct) else float(str(pct).replace('%',''))})

  df = pd.DataFrame(data).sort_values(["state","year"])
  return df

def upsert(df: pd.DataFrame):
  with ENGINE.begin() as conn:
    conn.execute(text("""
      create table if not exists car_ownership_by_state(
        state text not null,
        year  int  not null,
        number int not null,
        pct    numeric,
        primary key (state, year)
      );
    """))
    for rec in df.to_dict(orient="records"):
      conn.execute(text("""
        insert into car_ownership_by_state(state, year, number, pct)
        values(:state, :year, :number, :pct)
        on conflict (state, year)
        do update set number=excluded.number, pct=excluded.pct
      """), rec)

if __name__ == "__main__":
  df = load_all_states()
  upsert(df)
  print("✅ car_ownership_by_state rows:", len(df))
  print(df.head())
