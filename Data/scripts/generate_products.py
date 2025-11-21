import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
from database.session import OLTPSession
from sqlalchemy import text

# 商品品类
CATEGORIES = [
    (1, "Electronics", "电子产品"),
    (2, "Clothing", "服装鞋帽"), 
    (3, "Books", "图书文娱"),
    (4, "Home", "家居用品"),
    (5, "Sports", "运动户外")
]

def generate_products(num_products=50):
    print("🚀 开始生成商品数据...")
    session = OLTPSession()
    
    try:
        for i in range(num_products):
            category_id, category_en, category_zh = random.choice(CATEGORIES)
            
            # 根据不同品类设置价格范围
            if category_en == "Electronics":
                price = round(random.uniform(500, 3000), 2)
            elif category_en == "Clothing":
                price = round(random.uniform(50, 500), 2)
            else:
                price = round(random.uniform(20, 300), 2)
            
            cost = round(price * random.uniform(0.3, 0.7), 2)
            stock = random.randint(10, 100)
            
            session.execute(
                text("""
                    INSERT INTO products (product_name, category_id, category_name, price, cost, stock_quantity)
                    VALUES (:name, :category_id, :category_name, :price, :cost, :stock)
                """),
                {
                    'name': f"{category_zh}_{i:03d}",
                    'category_id': category_id,
                    'category_name': category_zh,
                    'price': price,
                    'cost': cost,
                    'stock': stock
                }
            )
            
            if i % 10 == 0:
                session.commit()
                print(f"📦 已生成 {i} 个商品...")
        
        session.commit()
        print(f"✅ 成功生成 {num_products} 个商品数据！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 生成商品数据时出错: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_products(50)  # 先生成50个测试