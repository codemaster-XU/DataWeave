# scripts/verify_data.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.session import OLTPSession
from sqlalchemy import text

print("📊 数据生成验证")
print("=" * 50)

session = OLTPSession()

try:
    # 验证用户数据
    result = session.execute(text("SELECT COUNT(*) as count FROM users"))
    user_count = result.scalar()
    print(f"👥 用户数量: {user_count}")
    
    # 验证商品数据
    result = session.execute(text("SELECT COUNT(*) as count FROM products"))
    product_count = result.scalar()
    print(f"📦 商品数量: {product_count}")
    
    # 查看商品分类分布
    result = session.execute(text("""
        SELECT category_name, COUNT(*) as count 
        FROM products 
        GROUP BY category_name
    """))
    print("🏷️ 商品分类分布:")
    for row in result:
        print(f"  - {row[0]}: {row[1]} 个")
    
    # 查看用户地域分布
    result = session.execute(text("""
        SELECT province, COUNT(*) as count 
        FROM users 
        GROUP BY province
    """))
    print("🌍 用户地域分布:")
    for row in result:
        print(f"  - {row[0]}: {row[1]} 人")
    
    if user_count > 0 and product_count > 0:
        print("🎉 数据生成验证通过!")
    else:
        print("❌ 数据生成存在问题")
        
except Exception as e:
    print(f"❌ 数据验证失败: {e}")
finally:
    session.close()