# reset_database.py
import os
from dotenv import load_dotenv
from database.session import OLTPSession, oltp_engine
from sqlalchemy import text

load_dotenv()

print("🔄 清理并重建数据库表")
print("=" * 50)

session = OLTPSession()

try:
    # 获取所有用户表（排除SQLite系统表）
    result = session.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """))
    existing_tables = [row[0] for row in result]
    
    print(f"📊 现有用户表: {existing_tables}")
    
    # 禁用外键约束（SQLite方式）
    session.execute(text("PRAGMA foreign_keys = OFF"))
    
    # 按依赖顺序删除表（先删子表，后删父表）
    tables_to_drop = ['order_items', 'orders', 'products', 'users']
    
    for table in tables_to_drop:
        if table in existing_tables:
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"✅ 删除表: {table}")
            except Exception as e:
                print(f"⚠️ 删除表 {table} 时出错: {e}")
    
    # 启用外键约束
    session.execute(text("PRAGMA foreign_keys = ON"))
    session.commit()
    
    # 重新创建表
    with open('scripts/create_tables.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # 分割SQL语句并执行
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    
    for statement in statements:
        if statement:  # 确保不是空字符串
            try:
                session.execute(text(statement))
                print(f"✅ 执行SQL: {statement[:50]}...")  # 只显示前50个字符
            except Exception as e:
                print(f"⚠️ 执行SQL时出错: {e}")
    
    session.commit()
    print("✅ 数据库表创建完成")
    
    # 验证表创建（SQLite方式）
    result = session.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """))
    tables_created = [row[0] for row in result]
    print(f"📊 创建的表: {tables_created}")
    
    expected_tables = ['users', 'products', 'orders', 'order_items']
    missing_tables = [table for table in expected_tables if table not in tables_created]
    
    if missing_tables:
        print(f"❌ 缺少表: {missing_tables}")
    else:
        print("🎉 所有表创建成功!")
        
except Exception as e:
    session.rollback()
    print(f"❌ 数据库重置失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()