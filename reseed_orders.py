import random
import sqlite3
from datetime import datetime, timedelta, date

DB_PATH = "ecommerce.db"


def create_tables(cur):
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            email TEXT,
            registration_date DATETIME,
            last_login DATETIME,
            status TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            price REAL,
            cost REAL,
            stock_quantity INTEGER,
            status TEXT,
            created_at DATETIME
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            order_date DATETIME,
            total_amount REAL,
            status TEXT,
            payment_method TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL
        )"""
    )


def seed_users(cur, n=120):
    cur.execute("DELETE FROM users")
    for i in range(1, n + 1):
        cur.execute(
            "INSERT INTO users(user_id, username, email, registration_date, last_login, status) VALUES (?,?,?,?,?,?)",
            (
                i,
                f"user{i}",
                f"user{i}@example.com",
                datetime.now() - timedelta(days=random.randint(30, 400)),
                datetime.now() - timedelta(days=random.randint(1, 30)),
                "active" if random.random() > 0.1 else "inactive",
            ),
        )


def seed_products(cur):
    categories = [
        ("电子产品", 800, 3000),
        ("服装", 80, 400),
        ("家居", 120, 800),
        ("美妆", 60, 500),
        ("食品", 20, 120),
    ]
    cur.execute("DELETE FROM products")
    pid = 1
    for cat, low, high in categories:
        for _ in range(10):
            price = round(random.uniform(low, high), 2)
            cur.execute(
                "INSERT INTO products(product_id, product_name, category, price, cost, stock_quantity, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    pid,
                    f"{cat}商品{pid}",
                    cat,
                    price,
                    round(price * random.uniform(0.4, 0.7), 2),
                    random.randint(50, 400),
                    "active",
                    datetime.now() - timedelta(days=random.randint(30, 400)),
                ),
            )
            pid += 1


def seed_orders(cur, start: date, end: date):
    cur.execute("DELETE FROM orders")
    cur.execute("DELETE FROM order_items")

    order_id = 1
    item_id = 1
    products = cur.execute("SELECT product_id, price, category FROM products").fetchall()
    product_ids = [p[0] for p in products]
    price_map = {p[0]: p[1] for p in products}
    day = start
    while day <= end:
        # weekday vs weekend volumes
        count = random.randint(20, 45) if day.weekday() < 5 else random.randint(35, 65)
        for _ in range(count):
            user_id = random.randint(1, 120)
            items = random.randint(1, 3)
            total = 0
            chosen = random.choices(product_ids, k=items)
            for pid in chosen:
                qty = random.randint(1, 2)
                price = price_map[pid]
                total += price * qty
                cur.execute(
                    "INSERT INTO order_items(item_id, order_id, product_id, quantity, unit_price) VALUES (?,?,?,?,?)",
                    (item_id, order_id, pid, qty, price),
                )
                item_id += 1
            cur.execute(
                "INSERT INTO orders(order_id, user_id, order_date, total_amount, status, payment_method) VALUES (?,?,?,?,?,?)",
                (
                    order_id,
                    user_id,
                    datetime.combine(day, datetime.min.time()) + timedelta(hours=random.randint(8, 21), minutes=random.randint(0, 59)),
                    round(total, 2),
                    random.choice(["delivered", "shipped", "pending"]),
                    random.choice(["支付宝", "微信支付", "银行卡"]),
                ),
            )
            order_id += 1
        day += timedelta(days=1)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    create_tables(cur)
    seed_users(cur)
    seed_products(cur)
    start = date.today() - timedelta(days=120)
    end = date.today()
    seed_orders(cur, start, end)
    conn.commit()
    conn.close()
    print(f"Reseeded users/products/orders/order_items with data from {start} to {end}")


if __name__ == "__main__":
    main()
