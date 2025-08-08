# etl/fetch_sensors.py
import requests
import pandas as pd
from pandas import json_normalize

BASE_URL = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/on-street-parking-bay-sensors/records"
PAGE_SIZE = 100
TOTAL = 3309   # 你页面左上角显示的 records 数，先写死；也可以先请求一页拿 total_count

def fetch_all():
    all_rows = []
    for offset in range(0, TOTAL, PAGE_SIZE):
        url = f"{BASE_URL}?limit={PAGE_SIZE}&offset={offset}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        results = data.get("results", [])
        if not results:
            break

        # 结果结构可能不同：有的在 results[*]['fields']，有的直接平铺
        if "fields" in results[0]:
            rows = [rec["fields"] for rec in results]
        elif "record" in results[0]:
            rows = [rec["record"] for rec in results]
        else:
            rows = results  # 直接平铺

        all_rows.extend(rows)
        print(f"fetched {offset} ~ {offset+PAGE_SIZE}")

    df = json_normalize(all_rows)
    # 统一挑一些常用字段（存在就保留）
    keep = [
        "bay_id", "status", "status_description", "status_timestamp", "statusupdated",
        "zone_number", "kerbsideid", "streetname", "rd_seg_dsc",
        "location.lat", "location.lon", "lat", "lon"   # 不同结构兜底
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep] if keep else df

if __name__ == "__main__":
    df = fetch_all()
    out = "data/sensors_raw.csv"
    df.to_csv(out, index=False)
    print(f"saved: {out}  ({len(df)} rows)")
    print(df.head())
