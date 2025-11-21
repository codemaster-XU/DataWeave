# -*- coding: utf-8 -*-
"""
轻量级电商数据分析后台
- SQLite 用作演示数据源，接口与 MySQL 类似
- 提供仪表盘、SQL 查询、数据导入等 API
"""

import http.server
import socketserver
import json
import sqlite3
from datetime import datetime, timedelta
import random
import os
import urllib.parse
import pandas as pd
import io
import re
import time
from typing import List, Dict, Any


class DatabaseManager:
    def __init__(self, db_path: str = "ecommerce.db") -> None:
        self.db_path = db_path
        self.allowed_tables = ("users", "products", "orders", "order_items")
        self.ensure_database()

    def get_connection(self) -> sqlite3.Connection:
        """Return a sqlite3 connection; caller must close it."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_database(self) -> None:
        """Create tables when missing and seed with demo data."""
        conn = self.get_connection()
        cursor = conn.cursor()

        tables_sql = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                registration_date DATETIME,
                last_login DATETIME,
                status TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT,
                category TEXT,
                price REAL,
                cost REAL,
                stock_quantity INTEGER,
                status TEXT,
                created_at DATETIME
            )""",
            """CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                order_date DATETIME,
                total_amount REAL,
                status TEXT,
                payment_method TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_price REAL
            )""",
        ]

        for sql in tables_sql:
            cursor.execute(sql)

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            self.insert_sample_data(cursor)
            conn.commit()

        conn.close()

    def insert_sample_data(self, cursor: sqlite3.Cursor) -> None:
        """Insert demo dataset for dashboard and query demos."""
        for i in range(50):
            cursor.execute(
                "INSERT INTO users (user_id, username, email, registration_date, last_login, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    i + 1,
                    f"user{i+1}",
                    f"user{i+1}@example.com",
                    self.random_date(365),
                    self.random_date(30),
                    "active" if random.random() > 0.1 else "inactive",
                ),
            )

        categories = ["电子产品", "服装", "家居", "美妆", "食品"]
        for i in range(30):
            category = random.choice(categories)
            price = round(random.uniform(10, 1000), 2)
            cursor.execute(
                "INSERT INTO products (product_id, product_name, category, price, cost, stock_quantity, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    i + 1,
                    f"{category}商品{i+1}",
                    category,
                    price,
                    round(price * random.uniform(0.3, 0.7), 2),
                    random.randint(0, 500),
                    "active",
                    self.random_date(365),
                ),
            )

        payment_methods = ["支付宝", "微信支付", "银行卡"]
        for order_id in range(1, 101):
            user_id = random.randint(1, 50)
            order_date = self.random_date(90)
            status = random.choices(["delivered", "shipped", "pending"], weights=[70, 20, 10])[0]
            payment_method = random.choice(payment_methods)
            total_amount = round(random.uniform(50, 2000), 2)

            cursor.execute(
                "INSERT INTO orders (order_id, user_id, order_date, total_amount, status, payment_method) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (order_id, user_id, order_date, total_amount, status, payment_method),
            )

            for _ in range(1, random.randint(1, 4)):
                product_id = random.randint(1, 30)
                quantity = random.randint(1, 3)
                cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
                result = cursor.fetchone()
                unit_price = result[0] if result else round(random.uniform(10, 500), 2)

                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, quantity, unit_price),
                )

    def random_date(self, days_back: int) -> datetime:
        return datetime.now() - timedelta(days=random.randint(0, days_back))

    def execute_query(self, query: str, params: tuple | None = None) -> List[Dict[str, Any]]:
        """Execute a query and return rows as dict."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [description[0] for description in cursor.description] if cursor.description else []
        results = [dict(zip(columns, row)) for row in cursor.fetchall()] if columns else []
        conn.close()
        return results

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        return self.execute_query(f"PRAGMA table_info({table_name})")

    def get_table_row_count(self, table_name: str) -> int:
        result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]["count"] if result else 0

    def get_all_tables(self) -> List[str]:
        tables = self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        return [table["name"] for table in tables]

    def import_csv_data(self, table_name: str, csv_content: str, row_limit: int = 5000) -> Dict[str, Any]:
        """Import CSV to a whitelisted table with basic validation."""
        if table_name not in self.allowed_tables:
            return {"success": False, "error": "不支持的表名"}

        try:
            df = pd.read_csv(io.StringIO(csv_content))
            # 清理列名首尾空格，避免因 CSV 空格导致匹配失败
            df.columns = df.columns.astype(str).str.strip()
        except Exception as exc:  # pragma: no cover - defensive
            return {"success": False, "error": f"CSV 解析失败: {exc}"}

        if len(df) == 0:
            return {"success": False, "error": "CSV 为空"}
        if len(df) > row_limit:
            return {"success": False, "error": f"单次导入最多 {row_limit} 行"}

        columns = [c["name"] for c in self.get_table_info(table_name)]
        unknown_columns = [col for col in df.columns if col not in columns]
        if unknown_columns:
            return {"success": False, "error": f"包含未知列: {', '.join(unknown_columns)}；期望列: {', '.join(columns)}"}

        # Ensure required PK exists if the CSV does not provide one (sqlite would auto-create ROWID otherwise)
        if "user_id" in columns and "user_id" not in df.columns and table_name == "users":
            return {"success": False, "error": "缺少用户主键 user_id"}

        conn = self.get_connection()
        try:
            # 采用追加模式，不再清空原有数据（避免覆盖原订单）
            df.to_sql(table_name, conn, if_exists="append", index=False)
            conn.commit()
            return {"success": True, "message": f"成功追加 {len(df)} 行数据到 {table_name}"}
        except Exception as exc:  # pragma: no cover - defensive
            conn.rollback()
            return {"success": False, "error": f"导入失败: {exc}"}
        finally:
            conn.close()


class DataAnalyzer:
    def __init__(self, db_path: str = "ecommerce.db") -> None:
        self.db = DatabaseManager(db_path)

    def get_dashboard_overview(self) -> Dict[str, Any]:
        try:
            tables = self.db.get_all_tables()
            orders_count = self.db.get_table_row_count("orders") if "orders" in tables else 0
            use_douyin = "douyin_sales" in tables and orders_count == 0
            if use_douyin:
                today_sql = """
                SELECT 
                    COUNT(*) as today_orders,
                    COALESCE(SUM(gmv), 0) as today_sales,
                    COUNT(*) as today_customers,
                    COALESCE(AVG(gmv), 0) as today_avg_order_value
                FROM douyin_sales
                WHERE DATE(date) = DATE('now','localtime')
                """
                monthly_sql = """
                SELECT 
                    COUNT(*) as monthly_orders,
                    COALESCE(SUM(gmv), 0) as monthly_sales,
                    COUNT(*) as monthly_customers
                FROM douyin_sales
                WHERE date >= DATE('now', '-30 days','localtime')
                """
            else:
                today_sql = """
                SELECT 
                    COUNT(*) as today_orders,
                    COALESCE(SUM(total_amount), 0) as today_sales,
                    COUNT(DISTINCT user_id) as today_customers,
                    COALESCE(AVG(total_amount), 0) as today_avg_order_value
                FROM orders 
                WHERE DATE(order_date) = DATE('now','localtime')
                  AND status != 'cancelled'
                """
                monthly_sql = """
                SELECT 
                    COUNT(*) as monthly_orders,
                    COALESCE(SUM(total_amount), 0) as monthly_sales,
                    COUNT(DISTINCT user_id) as monthly_customers
                FROM orders
                WHERE order_date >= DATE('now', '-30 days','localtime')
                  AND status != 'cancelled'
                """

            today_data = self.db.execute_query(today_sql)
            monthly_data = self.db.execute_query(monthly_sql)
            return {
                "today_metrics": today_data[0] if today_data else {},
                "monthly_metrics": monthly_data[0] if monthly_data else {},
            }
        except Exception:
            # Return fallback numbers to keep UI alive
            return {
                "today_metrics": {
                    "today_orders": 18,
                    "today_sales": 12560.50,
                    "today_customers": 15,
                    "today_avg_order_value": 697.81,
                },
                "monthly_metrics": {
                    "monthly_orders": 245,
                    "monthly_sales": 187920.75,
                    "monthly_customers": 189,
                },
            }

    def get_sales_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        try:
            tables = self.db.get_all_tables()
            orders_count = self.db.get_table_row_count("orders") if "orders" in tables else 0
            if "douyin_sales" in tables and orders_count == 0:
                sql = f"""
                SELECT 
                    DATE(date,'localtime') as date,
                    COUNT(*) as order_count,
                    COALESCE(SUM(gmv), 0) as daily_sales,
                    COALESCE(AVG(gmv), 0) as avg_order_value
                FROM douyin_sales
                WHERE date >= DATE('now', '-{days} days','localtime')
                GROUP BY DATE(date,'localtime')
                ORDER BY date
                """
            else:
                sql = f"""
                SELECT 
                    DATE(order_date,'localtime') as date,
                    COUNT(*) as order_count,
                    COALESCE(SUM(total_amount), 0) as daily_sales,
                    COALESCE(AVG(total_amount), 0) as avg_order_value
                FROM orders 
                WHERE order_date >= DATE('now', '-{days} days','localtime')
                  AND status != 'cancelled'
                GROUP BY DATE(order_date,'localtime')
                ORDER BY date
                """
            result = self.db.execute_query(sql)
            return result or self.generate_sample_sales_data(days)
        except Exception:
            return self.generate_sample_sales_data(days)

    def generate_sample_sales_data(self, days: int) -> List[Dict[str, Any]]:
        data = []
        base_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            order_count = random.randint(5, 20)
            daily_sales = round(random.uniform(3000, 15000), 2)
            data.append(
                {
                    "date": date,
                    "order_count": order_count,
                    "daily_sales": daily_sales,
                    "avg_order_value": round(daily_sales / order_count, 2),
                }
            )
        return data

    def get_category_analysis(self) -> List[Dict[str, Any]]:
        try:
            sql = """
            SELECT 
                p.category,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.quantity * oi.unit_price) as total_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status != 'cancelled'
            GROUP BY p.category
            ORDER BY total_revenue DESC
            """
            result = self.db.execute_query(sql)
            return result or self.generate_sample_category_data()
        except Exception:
            return self.generate_sample_category_data()

    def generate_sample_category_data(self) -> List[Dict[str, Any]]:
        categories = ["电子产品", "服装", "家居", "美妆", "食品"]
        data = []
        for category in categories:
            data.append(
                {
                    "category": category,
                    "order_count": random.randint(50, 200),
                    "total_quantity": random.randint(200, 800),
                    "total_revenue": round(random.uniform(50000, 200000), 2),
                }
            )
        return data

    def get_custom_query(self, sql_query: str, row_limit: int = 500) -> Dict[str, Any] | List[Dict[str, Any]]:
        """Guardrail: only allow SELECT/WITH queries and cap result size."""
        clean_query = sql_query.strip().rstrip(";")
        if not clean_query:
            return {"error": "SQL 不能为空"}
        if len(clean_query) > 2000:
            return {"error": "SQL 过长，请精简后再试"}
        if ";" in clean_query:
            return {"error": "不支持多条语句"}
        if re.search(r"\b(insert|update|delete|drop|alter|truncate|create|attach|pragma)\b", clean_query, re.I):
            return {"error": "出于安全考虑，仅支持查询语句(SELECT/WITH)"}
        if not re.match(r"^(select|with)\b", clean_query, re.I):
            return {"error": "仅允许 SELECT/WITH 查询"}
        if " order_items " in clean_query.lower() and "join" not in clean_query.lower():
            # gentle reminder when querying detail table alone
            pass
        if re.search(r"\blimit\b", clean_query, re.I) is None:
            clean_query = f"{clean_query} LIMIT {row_limit}"
        try:
            return self.db.execute_query(clean_query)
        except Exception as exc:
            return {"error": str(exc)}

    def get_database_info(self) -> Dict[str, Any]:
        tables = self.db.get_all_tables()
        table_info: Dict[str, Any] = {}
        for table in tables:
            table_info[table] = {
                "row_count": self.db.get_table_row_count(table),
                "columns": self.db.get_table_info(table),
            }
        return table_info

    def get_douyin_trend(self) -> List[Dict[str, Any]]:
        """Return daily metrics from douyin_sales if exists; fallback to orders."""
        try:
            tables = self.db.get_all_tables()
            if "douyin_sales" in tables:
                sql = """
                SELECT date(date,'localtime') as date, gmv, order_count, paying_users, refund_rate, aov
                FROM douyin_sales
                ORDER BY date
                """
                return self.db.execute_query(sql)
            # fallback: aggregate orders table
            sql = """
            SELECT 
                DATE(order_date) as date,
                SUM(total_amount) as gmv,
                COUNT(*) as order_count,
                COUNT(DISTINCT user_id) as paying_users,
                0 as refund_rate,
                COALESCE(AVG(total_amount),0) as aov
            FROM orders
            GROUP BY DATE(order_date)
            ORDER BY date
            """
            return self.db.execute_query(sql)
        except Exception:
            return []

    def get_day_orders(self, day: str) -> List[Dict[str, Any]]:
        """Return order-level detail for a given date (from orders/order_items)."""
        try:
            sql = """
            SELECT 
                o.order_id,
                o.user_id,
                o.order_date,
                o.total_amount,
                o.status,
                o.payment_method,
                COUNT(oi.item_id) as item_count,
                GROUP_CONCAT(DISTINCT p.category) as categories
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.product_id
            WHERE datetime(o.order_date) >= datetime(?, 'start of day')
              AND datetime(o.order_date) <  datetime(?, 'start of day', '+1 day')
            GROUP BY o.order_id
            ORDER BY o.order_date
            """
            return self.db.execute_query(sql, (day, day))
        except Exception:
            return []

    def get_order_day(self, day: str) -> List[Dict[str, Any]]:
        """Alias for day-level detail from orders (non-douyin)."""
        return self.get_day_orders(day)

    def get_order_day_stats(self, day: str) -> Dict[str, Any]:
        """Aggregated stats for a given day: category revenue/qty, hourly orders/sales, payment split."""
        stats = {"category": [], "hour": [], "payment": []}
        try:
            cat_sql = """
            SELECT p.category,
                   SUM(oi.quantity * oi.unit_price) AS revenue,
                   SUM(oi.quantity) AS qty
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE datetime(o.order_date) >= datetime(?, 'start of day')
              AND datetime(o.order_date) <  datetime(?, 'start of day', '+1 day')
            GROUP BY p.category
            ORDER BY revenue DESC
            """
            stats["category"] = self.db.execute_query(cat_sql, (day, day))

            hour_sql = """
            SELECT strftime('%H', o.order_date,'localtime') AS hour,
                   COUNT(*) AS orders,
                   SUM(o.total_amount) AS sales
            FROM orders o
            WHERE datetime(o.order_date) >= datetime(?, 'start of day')
              AND datetime(o.order_date) <  datetime(?, 'start of day', '+1 day')
            GROUP BY strftime('%H', o.order_date,'localtime')
            ORDER BY hour
            """
            stats["hour"] = self.db.execute_query(hour_sql, (day, day))

            pay_sql = """
            SELECT payment_method,
                   COUNT(*) AS orders,
                   SUM(total_amount) AS sales
            FROM orders
            WHERE datetime(order_date) >= datetime(?, 'start of day')
              AND datetime(order_date) <  datetime(?, 'start of day', '+1 day')
            GROUP BY payment_method
            ORDER BY orders DESC
            """
            stats["payment"] = self.db.execute_query(pay_sql, (day, day))
        except Exception:
            return stats
        return stats

    def import_data(self, table_name: str, csv_content: str) -> Dict[str, Any]:
        return self.db.import_csv_data(table_name, csv_content)

    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        if table_name not in self.db.allowed_tables:
            return [{"error": "不支持的表"}]
        return self.db.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")


class EcommerceHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.analyzer = DataAnalyzer()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Prefer the richer dashboard page when both versions exist.
        self.html_candidates = ("Untitled-2.html", "index.html")
        self.rate_limit_store = {}
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 120    # requests per IP per window
        super().__init__(*args, **kwargs)

    def _check_rate_limit(self):
        """Simple per-IP rate limiter (防“侏儒攻击”/小流量猛烈重复请求)."""
        client_ip = self.client_address[0] if self.client_address else "unknown"
        now = time.time()
        bucket = self.rate_limit_store.setdefault(client_ip, [])
        # 只保留窗口内的请求
        bucket[:] = [t for t in bucket if now - t <= self.rate_limit_window]
        if len(bucket) >= self.rate_limit_max:
            return False
        bucket.append(now)
        return True

    def do_OPTIONS(self):
        """Enable CORS preflight for POST."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if not self._check_rate_limit():
            self.send_error(429, "Too Many Requests")
            return
        if self.path == "/api/data/import":
            self.handle_data_import()
        else:
            self.send_error(404, "API not found")

    def handle_data_import(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode("utf-8"))
            table_name = payload.get("table_name")
            csv_content = payload.get("csv_content")

            if not table_name or not csv_content:
                self.send_json_response({"success": False, "error": "缺少表名或CSV数据"})
                return

            result = self.analyzer.import_data(table_name, csv_content)
            self.send_json_response(result)
        except Exception as exc:  # pragma: no cover - defensive
            self.send_json_response({"success": False, "error": str(exc)})

    def do_GET(self):
        if not self._check_rate_limit():
            self.send_error(429, "Too Many Requests")
            return
        if self.path == "/":
            self.serve_html()
        elif self.path.startswith("/api/"):
            self.handle_api_request()
        else:
            super().do_GET()

    def serve_html(self) -> None:
        """Serve dashboard HTML."""
        for filename in self.html_candidates:
            file_path = os.path.join(self.base_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
                return
        self.send_error(404, "未找到前端页面 (index.html / Untitled-2.html)")

    def handle_api_request(self) -> None:
        path = self.path
        if path == "/api/dashboard/overview":
            data = self.analyzer.get_dashboard_overview()
        elif path == "/api/sales/trend":
            data = self.analyzer.get_sales_trend()
        elif path == "/api/analysis/category":
            data = self.analyzer.get_category_analysis()
        elif path == "/api/database/info":
            data = self.analyzer.get_database_info()
        elif path == "/api/douyin/trend":
            data = self.analyzer.get_douyin_trend()
        elif path.startswith("/api/douyin/day/"):
            day = path.replace("/api/douyin/day/", "")
            data = self.analyzer.get_day_orders(day)
        elif path.startswith("/api/orders/day/"):
            day = path.replace("/api/orders/day/", "")
            data = self.analyzer.get_order_day(day)
        elif path.startswith("/api/orders-stats/day/"):
            day = path.replace("/api/orders-stats/day/", "")
            data = self.analyzer.get_order_day_stats(day)
        elif path.startswith("/api/data/sample/"):
            table_name = path.replace("/api/data/sample/", "")
            data = self.analyzer.get_sample_data(table_name)
        elif path.startswith("/api/query/"):
            query = urllib.parse.unquote(path.replace("/api/query/", ""))
            data = self.analyzer.get_custom_query(query)
        else:
            data = {"error": "API not found", "path": path}
        self.send_json_response(data)

    def send_json_response(self, data: Any) -> None:
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False, default=str, indent=2)
        self.wfile.write(response.encode("utf-8"))


def main() -> None:
    port = 8000
    with socketserver.TCPServer(("", port), EcommerceHandler) as httpd:
        print(f"✅ 服务器已启动: http://localhost:{port}")
        print("功能: 仪表盘 / 销售趋势 / 品类分析 / SQL 查询 / CSV 导入")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")


if __name__ == "__main__":
    main()
