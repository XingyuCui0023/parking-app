import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
ENGINE = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)

XLSX  = Path("app/data/vicpopulation2001-2021.xlsx")
SHEET = 0  # 或 "Table 4"

def tidy_from_wide():
  # 用第二行当表头（通常 2001..2021 能被识别为列名）
  df = pd.read_excel(XLSX, sheet_name=SHEET, header=1, engine="openpyxl")

  # 找到 Victoria & Greater Melb 那一行（兼容列名是否存在）
  name_col = df.columns[0]
  # 有的文件会有 "Greater Melb" 列辅助；没有也无所谓
  if "Greater Melb" in df.columns:
    row = df[(df[name_col].astype(str).str.strip().str.lower()=="victoria") &
             (df["Greater Melb"].astype(str).str.contains("Greater", case=False, na=False))]
    if row.empty:
      row = df[df[name_col].astype(str).str.strip().str.lower()=="victoria"].head(1)
  else:
    row = df[df[name_col].astype(str).str.strip().str.lower()=="victoria"].head(1)

  if row.empty:
    raise RuntimeError("找不到 Victoria 这一行")

  row = row.iloc[0]

  # 找所有 2001..2021 的列
  years = [c for c in df.columns if isinstance(c,(int,float)) and 2001<=int(c)<=2021]
  years = list(map(int, years))
  years.sort()

  recs = []
  for y in years:
    v = row[y]
    if pd.notna(v):
      recs.append({"year": int(y), "residents": int(v)})

  out = pd.DataFrame(recs).sort_values("year")
  return out

def upsert(df: pd.DataFrame):
  with ENGINE.begin() as conn:
    conn.execute(text("""
      create table if not exists population_cbd(
        year int primary key,
        residents bigint not null
      );
    """))
    for rec in df.to_dict(orient="records"):
      conn.execute(text("""
        insert into population_cbd(year, residents)
        values(:year, :residents)
        on conflict (year) do update set residents=excluded.residents
      """), rec)

if __name__ == "__main__":
  df = tidy_from_wide()
  upsert(df)
  print("✅ population_cbd rows:", len(df))
  print(df.head(), " ... ", df.tail())
