import random
import sqlite3
from datetime import date, timedelta

DB_PATH = "ecommerce.db"


def month_base(month: int) -> float:
    """Rough seasonal base GMV by month (元)."""
    bases = {
        1: 150_000,
        2: 130_000,
        3: 125_000,  # 3.8节及春季回暖
        4: 115_000,
        5: 120_000,
        6: 135_000,  # 618
        7: 115_000,
        8: 118_000,
        9: 125_000,
        10: 128_000,
        11: 170_000,  # 双11
        12: 175_000,  # 年末旺季
    }
    return bases.get(month, 120_000)


def promo_multiplier(d: date) -> float:
    """Add spikes around典型大促."""
    year = d.year
    promos = [
        (date(year, 3, 6), date(year, 3, 9), 1.12),   # 女王节
        (date(year, 6, 15), date(year, 6, 19), 1.18),  # 618
        (date(year, 9, 7), date(year, 9, 11), 1.12),   # 99
        (date(year, 11, 1), date(year, 11, 12), 1.25), # 双11
        (date(year, 12, 10), date(year, 12, 13), 1.12),# 双12
        (date(year, 12, 20), date(year, 12, 31), 1.15),# 年末
        (date(year, 1, 1), date(year, 1, 3), 1.15),    # 元旦
    ]
    for start, end, mult in promos:
        if start <= d <= end:
            return mult
    return 1.0


def generate_rows(start: date, end: date):
    random.seed(20231201)
    d = start
    rows = []
    while d <= end:
        base_gmv = month_base(d.month)
        weekend_boost = 1.1 if d.weekday() >= 5 else 1.0
        promo = promo_multiplier(d)
        noise = random.uniform(0.9, 1.12)
        gmv = base_gmv * weekend_boost * promo * noise

        # aov 随月份波动，旺季略高
        if d.month in (11, 12):
            aov = random.uniform(150, 240)
        elif d.month in (6, 9):
            aov = random.uniform(130, 210)
        else:
            aov = random.uniform(110, 190)

        order_count = max(1, int(gmv / aov))
        paying_users = max(1, int(order_count * random.uniform(0.7, 0.86)))
        refund_rate = random.uniform(0.008, 0.035)
        refund_count = max(0, int(order_count * refund_rate))

        rows.append(
            (
                d.isoformat(),
                "Douyin",
                round(gmv, 2),
                order_count,
                paying_users,
                refund_count,
                round(refund_rate, 4),
                round(gmv / order_count, 2),
            )
        )
        d += timedelta(days=1)
    return rows


def main():
    start = date(2023, 12, 1)
    end = date.today()
    rows = generate_rows(start, end)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
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
        """
    )
    cur.execute("DELETE FROM douyin_sales")
    cur.executemany(
        """
        INSERT INTO douyin_sales
        (date, platform, gmv, order_count, paying_users, refund_count, refund_rate, aov)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows)} rows ({start} ~ {end}) into douyin_sales in {DB_PATH}")


if __name__ == "__main__":
    main()
