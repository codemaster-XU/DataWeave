import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
from faker import Faker
from database.session import OLTPSession
from sqlalchemy import text

fake = Faker('zh_CN')

# 中国省市数据
PROVINCES_CITIES = {
    "北京市": ["北京市"],
    "上海市": ["上海市"], 
    "广东省": ["广州市", "深圳市", "东莞市"],
    "浙江省": ["杭州市", "宁波市", "温州市"],
    "江苏省": ["南京市", "苏州市", "无锡市"]
}

def generate_users(num_users=100):
    print("🚀 开始生成用户数据...")
    session = OLTPSession()
    
    try:
        for i in range(num_users):
            province = random.choice(list(PROVINCES_CITIES.keys()))
            city = random.choice(PROVINCES_CITIES[province])
            
            session.execute(
                text("""
                    INSERT INTO users (username, registration_date, province, city)
                    VALUES (:username, :reg_date, :province, :city)
                """),
                {
                    'username': f"user_{i:04d}",
                    'reg_date': fake.date_between(start_date='-2y', end_date='today'),
                    'province': province,
                    'city': city
                }
            )
            
            if i % 20 == 0:
                session.commit()
                print(f"📊 已生成 {i} 个用户...")
        
        session.commit()
        print(f"✅ 成功生成 {num_users} 个用户数据！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 生成用户数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    generate_users(100)  # 生成100个用户