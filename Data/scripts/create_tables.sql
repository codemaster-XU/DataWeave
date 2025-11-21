-- Active: 1763711657033@@127.0.0.1@3306
-- scripts/create_tables.sql
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50),
    registration_date DATE,
    province VARCHAR(50),
    city VARCHAR(50)
);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name VARCHAR(100),
    category_id INTEGER,
    category_name VARCHAR(50),
    price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    stock_quantity INTEGER
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    order_date DATETIME,
    total_amount DECIMAL(10, 2),
    order_status TINYINT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    item_price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);