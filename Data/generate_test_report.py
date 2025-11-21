# generate_test_report.py
import os
import sys
from urllib.request import urlopen
from urllib.error import URLError
import json

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database.session import OLTPSession
from sqlalchemy import text
from datetime import datetime

print("📈 电商平台测试报告")
print("=" * 60)

# 数据库统计
session = OLTPSession()
try:
    # 用户统计
    result = session.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()
    
    result = session.execute(text("""
        SELECT province, COUNT(*) as count 
        FROM users 
        GROUP BY province 
        ORDER BY count DESC
    """))
    user_by_province = {row[0]: row[1] for row in result}
    
    # 商品统计
    result = session.execute(text("SELECT COUNT(*) FROM products"))
    product_count = result.scalar()
    
    result = session.execute(text("""
        SELECT category_name, COUNT(*) as count,
               AVG(price) as avg_price, AVG(cost) as avg_cost
        FROM products 
        GROUP BY category_name
    """))
    products_by_category = []
    for row in result:
        avg_price = float(row[2]) if row[2] else 0
        avg_cost = float(row[3]) if row[3] else 0
        margin = ((avg_price - avg_cost) / avg_price * 100) if avg_price > 0 else 0
        
        products_by_category.append({
            'category': row[0],
            'count': row[1],
            'avg_price': avg_price,
            'avg_cost': avg_cost,
            'margin': margin
        })
    
    # 订单统计
    result = session.execute(text("SELECT COUNT(*) FROM orders"))
    order_count = result.scalar()
    
    result = session.execute(text("SELECT SUM(total_amount) FROM orders"))
    total_sales = result.scalar() or 0
    
    print(f"👥 用户统计:")
    print(f"  - 总用户数: {user_count}")
    print(f"  - 地域分布:")
    for province, count in user_by_province.items():
        percentage = (count / user_count * 100) if user_count > 0 else 0
        print(f"    * {province}: {count} 人 ({percentage:.1f}%)")
    
    print(f"\n📦 商品统计:")
    print(f"  - 总商品数: {product_count}")
    print(f"  - 分类详情:")
    for cat in products_by_category:
        print(f"    * {cat['category']}: {cat['count']} 个, 均价 ¥{cat['avg_price']:.2f}, 毛利 {cat['margin']:.1f}%")
    
    print(f"\n💰 订单统计:")
    print(f"  - 总订单数: {order_count}")
    print(f"  - 总销售额: ¥{total_sales:.2f}")
    
finally:
    session.close()

# API服务统计
print(f"\n🌐 API服务状态:")
try:
    response = urlopen("http://localhost:5000/api/health", timeout=5)
    if response.status == 200:
        data = json.loads(response.read().decode())
        print(f"  - 服务状态: ✅ 运行正常")
        print(f"  - 服务信息: {data.get('service', '未知')}")
        
        # 获取仪表板统计
        try:
            response = urlopen("http://localhost:5000/api/stats/dashboard", timeout=5)
            stats = json.loads(response.read().decode())
            print(f"  - 总用户数: {stats.get('total_users', 0)}")
            print(f"  - 总商品数: {stats.get('total_products', 0)}")
            print(f"  - 总订单数: {stats.get('total_orders', 0)}")
            print(f"  - 总销售额: ¥{stats.get('total_sales', 0):.2f}")
        except:
            print(f"  - 仪表板API: ❌ 无法获取详细统计")
            
    else:
        print(f"  - 服务状态: ❌ 异常 (状态码: {response.status})")
        
except URLError as e:
    print(f"  - 服务状态: ❌ 连接失败")
    print(f"  - 错误信息: {e}")
    print(f"  - 解决方案: 请运行 'python services/api.py' 启动API服务")

print(f"\n⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 总体评估
print("📊 总体评估:")
if user_count > 0 and product_count > 0:
    print("🎉 数据库: ✅ 数据完整")
else:
    print("⚠️  数据库: 数据不完整，请运行数据生成脚本")

try:
    urlopen("http://localhost:5000/api/health", timeout=2)
    print("🎉 API服务: ✅ 运行正常")
except:
    print("⚠️  API服务: ❌ 未运行")

print("🎯 测试完成!")