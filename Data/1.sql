-- Active: 1763711657033@@127.0.0.1@3306
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 产品表
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 插入示例数据
INSERT INTO users (username, password_hash, email) VALUES 
('admin', 'hashed_password_123', 'admin@shop.com'),
('john_doe', 'hashed_password_456', 'john@example.com');

INSERT INTO products (name, description, price, stock_quantity, category) VALUES 
('MacBook Pro', '13-inch Apple MacBook Pro', 12999.00, 5, 'Electronics'),
('iPhone 15', 'Latest Apple iPhone', 7999.00, 10, 'Electronics'),
('Coffee Maker', 'Automatic coffee machine', 899.00, 15, 'Home Appliances');