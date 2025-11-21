import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 从环境变量获取数据库路径，如果不存在则使用默认路径
db_path = os.getenv('DB_PATH', r"d:\Mine\数据库\shop.db")

# 创建 SQLite 数据库连接
oltp_engine = create_engine(f"sqlite:///{db_path}")
OLTPSession = sessionmaker(bind=oltp_engine)

print(f"✅ SQLite 数据库连接配置完成! 数据库路径: {db_path}")