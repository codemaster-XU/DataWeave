# test_setup.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("🔧 环境准备检查")
print("=" * 50)

# 检查环境变量
required_env_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME_OLTP']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ 缺少环境变量: {missing_vars}")
    print("请检查 .env 文件配置")
    sys.exit(1)
else:
    print("✅ 环境变量配置完整")

# 检查Python包
required_packages = ['faker', 'sqlalchemy', 'pymysql', 'flask', 'flask_cors']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f"❌ 缺少Python包: {missing_packages}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("✅ Python依赖包完整")

print("🎉 环境准备检查通过!")