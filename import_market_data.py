import csv
import os
import sqlite3
from datetime import datetime

DB = os.getenv("DATABASE_PATH", "carflip.db")
CSV_PATH = os.getenv("MARKET_CSV", "market_stats.csv")

required = {
    "city", "state", "make", "model", "sold_count",
    "bought_count", "avg_price", "avg_days_to_sell", "period_days"
}

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"Missing CSV columns: {', '.join(sorted(missing))}")

    with sqlite3.connect(DB) as conn:
        for row in reader:
            conn.execute("""
                INSERT INTO market_stats
                (city,state,make,model,sold_count,bought_count,avg_price,
                 avg_days_to_sell,period_days,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                row["city"], row["state"], row["make"], row["model"],
                int(row["sold_count"]), int(row["bought_count"]),
                float(row["avg_price"]), float(row["avg_days_to_sell"]),
                int(row["period_days"]), datetime.utcnow().isoformat()
            ))
print("Market data imported.")
