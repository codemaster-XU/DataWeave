# test_database.py
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

print("🗄️ 数据库连接测试")
print("=" * 50)

try:
    from database.session import oltp_engine, OLTPSession
    
    # 测试基础连接
    with oltp_engine.connect() as conn:
        # 使用 SQLite 的正确函数
        result = conn.execute(text('SELECT sqlite_version() as version'))
        version = result.scalar()
        print(f"✅ SQLite版本: {version}")
        
        # SQLite 不需要 DATABASE() 函数，显示文件路径
        db_url = str(oltp_engine.url)
        print(f"✅ 数据库连接: {db_url}")
        
        # 检查所有表
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"✅ 数据库中的表: {tables}")
    
    # 测试会话
    session = OLTPSession()
    try:
        result = session.execute(text("SELECT 1 as test_value"))
        test_result = result.scalar()
        print(f"✅ 会话测试: {test_result}")
    finally:
        session.close()
        
    print("🎉 数据库连接测试通过!")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)