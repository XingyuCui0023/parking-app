import os, csv, math
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sensors_raw.csv")

def parse_ts(x: str):
    if not x:
        return None
    try:
        dt = datetime.fromisoformat(x.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def to_float(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    # 有些 csv 会带逗号或空格
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return None

def to_int_like(x):
    """把 '7394.0' / '7,394' / 7394 → 7394，异常返回 None"""
    f = to_float(x)
    if f is None or math.isnan(f):
        return None
    try:
        return int(round(f))
    except Exception:
        return None

def main():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            status_desc = (row.get("status_description") or row.get("status") or "").strip()
            ts = parse_ts(row.get("status_timestamp") or row.get("last_updated") or "")

            kerb = row.get("kerbsideid") or row.get("kerbside_id") or row.get("sensor_id")
            zone = row.get("zone_number") or row.get("zone")

            # 列名可能是 location.lat / location.lon 或 lat / lon
            lat = row.get("location.lat") or row.get("lat")
            lon = row.get("location.lon") or row.get("lon")

            kerb = to_int_like(kerb)
            zone = to_int_like(zone)
            lat = to_float(lat)
            lon = to_float(lon)

            if not (kerb and ts and lat is not None and lon is not None and
                    not math.isnan(lat) and not math.isnan(lon)):
                continue

            rows.append((kerb, zone, status_desc, ts, lat, lon))

    if not rows:
        print("No valid rows parsed. Check CSV headers?")
        return

    with psycopg2.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        # 1) 先写入基本列，冲突（相同 kerbsideid+timestamp）忽略
        execute_values(cur, """
            INSERT INTO sensor_status
             (kerbsideid, zone_number, status_description, status_timestamp, lat, lon)
            VALUES %s
            ON CONFLICT (kerbsideid, status_timestamp) DO NOTHING
        """, rows, page_size=2000)

        # 2) 统一补 geom
        cur.execute("""
            UPDATE sensor_status
               SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
             WHERE geom IS NULL AND lon IS NOT NULL AND lat IS NOT NULL;
        """)

    print(f"Inserted/considered {len(rows)} rows (duplicates skipped).")

if __name__ == "__main__":
    main()
