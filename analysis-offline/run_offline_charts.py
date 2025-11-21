import os
import sqlite3
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 针对现有 Web 作业产生的 SQLite 数据库
ANALYSIS_DB_PATH = Path(__file__).resolve().parent.parent / "ecommerce.db"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# A lighter, modern style for plots with moderate font sizes
sns.set_theme(context="notebook", style="whitegrid")
plt.rcParams.update({"font.size": 10})


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_table(query: str) -> pd.DataFrame:
    if not ANALYSIS_DB_PATH.exists():
        raise FileNotFoundError(f"未找到数据库: {ANALYSIS_DB_PATH}")
    with sqlite3.connect(ANALYSIS_DB_PATH) as conn:
        return pd.read_sql_query(query, conn, parse_dates=["order_date"], coerce_float=True)


def chart_orders_sales_trend():
    df = load_table(
        """
        SELECT DATE(order_date) AS dt,
               COUNT(*) AS order_cnt,
               SUM(total_amount) AS sales
        FROM orders
        GROUP BY DATE(order_date)
        ORDER BY dt
        """
    )
    df["dt"] = pd.to_datetime(df["dt"])
    # Smooth lines with a small rolling mean to reduce jaggedness
    df = df.sort_values("dt")
    df["sales_smooth"] = df["sales"].rolling(window=5, min_periods=1, center=True).mean()
    df["orders_smooth"] = df["order_cnt"].rolling(window=5, min_periods=1, center=True).mean()

    plt.figure(figsize=(13, 5))
    ax = sns.lineplot(
        df, x="dt", y="sales_smooth", label="Revenue (¥, smoothed)", color="#22d3ee", linewidth=2.2
    )
    ax2 = ax.twinx()
    sns.lineplot(
        df, x="dt", y="orders_smooth", label="Orders (smoothed)", color="#a855f7", ax=ax2, linewidth=2.0
    )
    # subtle area fills to improve readability
    ax.fill_between(df["dt"], df["sales_smooth"], alpha=0.12, color="#22d3ee")
    ax2.fill_between(df["dt"], 0, df["orders_smooth"], alpha=0.10, color="#a855f7")
    ax.set_ylabel("Revenue (¥)")
    ax2.set_ylabel("Orders")
    ax.legend(loc="upper left", fontsize=9)
    ax2.legend(loc="upper right", fontsize=9)
    # align baselines for readability
    ax.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)
    # limit tick clutter on x axis using date locator/formatter
    locator = mdates.AutoDateLocator(minticks=6, maxticks=12)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    plt.title("Orders & Revenue Trend")
    plt.xticks(rotation=25, ha="right", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax2.tick_params(axis="y", labelsize=9)
    plt.tight_layout()
    outfile = OUTPUT_DIR / "orders_sales_trend.png"
    plt.savefig(outfile, dpi=160)
    plt.close()
    return outfile


def chart_category_revenue():
    df = load_table(
        """
        SELECT p.category,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        GROUP BY p.category
        ORDER BY revenue DESC
        """
    )
    # Map categories to English to avoid font fallback/garbled labels
    category_map = {
        "电子产品": "Electronics",
        "服装": "Apparel",
        "家居": "Home",
        "美妆": "Beauty",
        "食品": "Food",
    }
    df["category_en"] = df["category"].map(category_map).fillna(df["category"])
    plt.figure(figsize=(6, 4))
    sns.barplot(df, y="category_en", x="revenue", hue="category_en", palette="viridis", legend=False)
    plt.title("Category Revenue")
    plt.xlabel("Revenue (¥)")
    plt.ylabel("Category")
    plt.tight_layout()
    outfile = OUTPUT_DIR / "category_revenue.png"
    plt.savefig(outfile, dpi=160)
    plt.close()
    return outfile


def chart_rfm():
    df = load_table(
        """
        SELECT u.user_id,
               julianday('now') - julianday(MAX(o.order_date)) AS recency,
               COUNT(o.order_id) AS frequency,
               SUM(o.total_amount) AS monetary
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.user_id
        """
    )
    df["recency"] = df["recency"].fillna(df["recency"].max() or 0)
    plt.figure(figsize=(8, 5))
    scatter = plt.scatter(
        df["recency"], df["frequency"], c=df["monetary"], cmap="cool", alpha=0.65, s=50, edgecolors="none"
    )
    cbar = plt.colorbar(scatter, label="Monetary (¥)")
    cbar.ax.tick_params(labelsize=9)
    plt.xlabel("Days Since Last Order (Recency)", fontsize=11)
    plt.ylabel("Order Count (Frequency)", fontsize=11)
    plt.title("RFM Scatter", fontsize=13)
    plt.xticks(fontsize=9)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    outfile = OUTPUT_DIR / "rfm_scatter.png"
    plt.savefig(outfile, dpi=160)
    plt.close()
    return outfile


def main():
    ensure_output_dir()
    outputs = [
        chart_orders_sales_trend(),
        chart_category_revenue(),
        chart_rfm(),
    ]
    print("[OK] Offline charts generated:")
    for path in outputs:
        print(f" - {path}")


if __name__ == "__main__":
    # 为了避免 GUI 阻塞，使用无交互后端
    os.environ["MPLBACKEND"] = "Agg"
    main()
