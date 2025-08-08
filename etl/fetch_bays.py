# etl/fetch_bays.py
import requests
import pandas as pd
from pandas import json_normalize

BASE_URL = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/on-street-parking-bays/records"
PAGE_SIZE = 100
TOTAL = 32000  # 这个数据集记录更多；先拉几千行试下，OK 再拉全量

def fetch_all(max_total=2000):
    all_rows = []
    for offset in range(0, max_total, PAGE_SIZE):
        url = f"{BASE_URL}?limit={PAGE_SIZE}&offset={offset}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            break

        if "fields" in results[0]:
            rows = [rec["fields"] for rec in results]
        elif "record" in results[0]:
            rows = [rec["record"] for rec in results]
        else:
            rows = results
        all_rows.extend(rows)
        print(f"fetched {offset} ~ {offset+PAGE_SIZE}")

    df = json_normalize(all_rows)
    keep = [
        "bay_id", "marker_id", "rd_seg_id", "rd_seg_dsc", "street_marker",
        "street_name", "sign_plate_id", "parking_zone", "location.lat", "location.lon", "lat", "lon"
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep] if keep else df

if __name__ == "__main__":
    df = fetch_all(max_total=5000)  # 先拉 5000 行验证
    out = "data/bays_raw.csv"
    df.to_csv(out, index=False)
    print(f"saved: {out}  ({len(df)} rows)")
    print(df.head())
