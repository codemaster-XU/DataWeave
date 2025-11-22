# 电商数据库分析中台

> 数据指标看板 + 订单明细 + 只读 SQL 工具 + CSV 追加导入  
> Author: Zongqi Xu · Email: zongqixu2025@163.com

## 快速运行
```bash
python "import mysql2.py"   # 启动 Python http.server + SQLite，默认端口 8000
# 可选：重置演示数据
python reseed_orders.py
```
浏览器访问：http://localhost:8000/

## 技术栈
- 后端：Python http.server + SQLite（见 `import mysql2.py`）
- 前端：原生 JS + ECharts（见 `Untitled-2.html`）
- 数据库：本地 `ecommerce.db`，核心表 `users`、`products`、`orders`、`order_items`，演示表 `douyin_sales`（可选）

## 功能一览
- 仪表盘：今日指标、近 30 日销售与订单趋势、品类销售占比
- 趋势下钻：点击某日，左侧展示当日订单明细，右侧展示品类/小时/支付方式三张统计图
- 数据管理：表结构与行数、样本预览、CSV 追加导入
- SQL 工具：只读 SELECT/WITH，一次一条，自动 LIMIT 500
- 主题切换：蓝 / 粉 / 黑

## 数据库关系模型
- 关系与键：
  - `users (user_id PK)` —< `orders (order_id PK, user_id FK)`
  - `products (product_id PK)` —< `order_items (item_id PK, product_id FK, order_id FK)`
  - 订单与明细：一对多；用户与订单：一对多；品类字段：`products.category`
- 典型查询：
  - 日销售额：`SELECT date(order_date), SUM(total_amount) FROM orders GROUP BY date(order_date);`
  - 品类销售：`orders` JOIN `order_items` JOIN `products` 聚合 revenue
  - 明细展开：`orders` JOIN `order_items` JOIN `products`

## 使用指南
### Web 端
- 仪表盘：今日指标、近 30 日趋势、品类占比
- 趋势点击：展开当日订单列表 + 品类/小时/支付方式三图
- 样本预览：四张核心表前几行
- SQL 工具：输入 SELECT/WITH（只读，自动 LIMIT 500）
- CSV 导入：选择表（users/products/orders/order_items），粘贴带表头 CSV，点击“导入数据”（追加模式，不清空）
  ```csv
  order_id,user_id,order_date,total_amount,status,payment_method
  93001,1,2025-11-21 10:00:00,199.99,delivered,支付宝
  ```
  *导入 orders 后需同步导入对应的 order_items，且 product_id 存在*

### sqlite3 命令行
```bash
# 查
sqlite3 ecommerce.db "SELECT * FROM orders LIMIT 5;"
sqlite3 ecommerce.db "SELECT date(order_date), SUM(total_amount) FROM orders GROUP BY date(order_date);"
# 增
sqlite3 ecommerce.db "INSERT INTO orders(order_id,user_id,order_date,total_amount,status,payment_method) VALUES (94000,1,'2025-11-21 10:15:00',299.00,'delivered','支付宝');"
sqlite3 ecommerce.db "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES (94000,1,1,299.00);"
# 改
sqlite3 ecommerce.db "UPDATE orders SET status='shipped' WHERE order_id=94000;"
# 删
sqlite3 ecommerce.db "DELETE FROM orders WHERE order_id=94000;"
# 备份
copy ecommerce.db ecommerce.bak.db
```

## 安全与防护
- 只读查询：后端 `get_custom_query` 仅允 SELECT/WITH，单条语句自动 LIMIT 500，拒绝 INSERT/UPDATE/DELETE/DDL
- CSV 校验：表名白名单、列名匹配（自动 trim）、行数 ≤ 5000，追加写入避免覆盖
- 速率限制：每 IP 60 秒内最多 120 次请求，超限返回 429（防小流量高频攻击）
- 参数化与前端校验：后端安全拼接，前端基本校验

## CSV 导入要点
- 追加模式：不会清空原表，请避免主键重复
- 列名需与表字段一致（自动去空格，未知列会提示期望列）
- 导入 orders 后请导入对应的 order_items，确保 product_id 已存在
- 日期格式示例：`YYYY-MM-DD HH:MM:SS`

## API 速查
- `/api/dashboard/overview` 今日/近期概览
- `/api/sales/trend` 近 30 日趋势
- `/api/analysis/category` 品类占比
- `/api/database/info` 表结构与行数
- `/api/data/sample/<table>` 样本预览
- `/api/query/<encoded-sql>` 只读 SQL
- `/api/data/import` CSV 导入（POST: table_name, csv_content）
- `/api/orders/day/<YYYY-MM-DD>` 当日订单明细
- `/api/orders-stats/day/<YYYY-MM-DD>` 当日统计（品类/小时/支付方式）
- `/api/douyin/trend` 若存在 douyin_sales 则返回，否则回退 orders 聚合

## 常见问题
- 导入后看板不变：确认 orders/order_items 落在近 30 天或今天；检查主键是否冲突  
  `SELECT COUNT(*) FROM orders WHERE date(order_date)=date('now');`
- CSV 未生效：列名不匹配或主键重复，按提示修正后重试
- 趋势点击跨天：后端已用 [当日 00:00:00, 次日 00:00:00) 过滤，仍有问题请检查 order_date 时区/格式
- 需重置演示数据：运行 `python reseed_orders.py` 后重启后端

## 数据库设计要点
- 规范化：用户 / 商品 / 订单 / 订单明细分表，主键/外键保证引用完整性
- 索引建议：`orders(user_id, order_date)`、`orders(order_date)`、`order_items(order_id)`、`order_items(product_id)`、`products(category)`、`users(status)`
- 事务与回滚：CSV 导入出错时回滚；在线查询保持只读
- 聚合与分组：品类/小时/支付方式统计均使用标准 SQL GROUP BY，便于迁移

## 防侏儒攻击（小流量高频）
- 简易限流：每 IP 60 秒内最多 120 次请求，超限返回 429
- 只读查询 + 自动 LIMIT，杜绝批量写入或资源耗尽
- CSV 行数与表白名单限制，防止瞬时大批量写入
