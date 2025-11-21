import sqlite3, random, math
from datetime import date, timedelta

DB = "ecommerce.db"
random.seed(20231201)

def gen_series():
    start, end = date(2023, 12, 1), date(2024, 1, 31)
    d = start
    rows = []
    while d <= end:
        # 设定基线随月份变化
        if d.month == 12:
            base_gmv = 125000  # 12 月中高位
        else:  # 1 月
            base_gmv = 115000  # 1 月略回落
        # 周末提振
        weekend_boost = 1.0 + (0.08 if d.weekday() >= 5 else 0.0)
        # 特殊档期小高峰
        promo = 1.0
        if date(2023,12,20) <= d <= date(2023,12,25):
            promo = 1.15
        if date(2023,12,30) <= d <= date(2024,1,2):
            promo = 1.18
        # 噪声
        noise = random.uniform(0.9, 1.12)
        gmv = base_gmv * weekend_boost * promo * noise

        # 客单价设定与 GMV 呼应
        aov = random.uniform(120, 210) if d.month == 12 else random.uniform(110, 190)
        order_count = max(1, int(gmv / aov))
        paying_users = max(1, int(order_count * random.uniform(0.7, 0.85)))

        refund_rate = random.uniform(0.008, 0.035)
        refund_count = max(0, int(order_count * refund_rate))

        rows.append((
            d.isoformat(),
            "Douyin",
            round(gmv, 2),
            order_count,
            paying_users,
            refund_count,
            round(refund_rate, 4),
            round(gmv / order_count, 2),
        ))
        d += timedelta(days=1)
    return rows

rows = gen_series()

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS douyin_sales (
  date TEXT PRIMARY KEY,
  platform TEXT,
  gmv REAL,
  order_count INTEGER,
  paying_users INTEGER,
  refund_count INTEGER,
  refund_rate REAL,
  aov REAL
)
""")
cur.execute("DELETE FROM douyin_sales")  # 如需保留旧数据请注释这一行
cur.executemany("""
INSERT INTO douyin_sales (date, platform, gmv, order_count, paying_users, refund_count, refund_rate, aov)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", rows)
conn.commit()
conn.close()
print(f"Inserted {len(rows)} rows into douyin_sales in {DB}")
