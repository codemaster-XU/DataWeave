# full_integration_test.py
import json
import time
import sys
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "http://localhost:5000/api"

def test_endpoint(endpoint, expected_key=None):
    """测试单个API端点"""
    try:
        response = urlopen(f"{BASE_URL}/{endpoint}", timeout=5)
        if response.status == 200:
            data = json.loads(response.read().decode())
            print(f"✅ GET /{endpoint}: 成功")
            if expected_key and expected_key in data:
                print(f"   📊 {expected_key}: {data[expected_key]}")
            return True
        else:
            print(f"❌ GET /{endpoint}: 失败 (状态码: {response.status})")
            return False
    except Exception as e:
        print(f"❌ GET /{endpoint}: 错误 ({e})")
        return False

def test_health():
    """测试健康检查端点"""
    try:
        response = urlopen(f"{BASE_URL}/health", timeout=2)
        data = json.loads(response.read().decode())
        print("✅ API服务正在运行")
        print(f"   📊 服务状态: {data.get('status', '未知')}")
        return True
    except URLError as e:
        print(f"❌ API服务未启动，请运行: python services/api.py")
        print(f"   错误详情: {e}")
        return False

print("🧪 完整集成测试")
print("=" * 50)

# 检查API服务是否运行
if not test_health():
    sys.exit(1)

# 测试所有端点
endpoints = [
    ("health", "status"),
    ("stats/dashboard", "total_users"),
    ("users", "users"),
    ("products/top-selling", None)
]

all_passed = True
for endpoint, key in endpoints:
    if not test_endpoint(endpoint, key):
        all_passed = False

print("=" * 50)
if all_passed:
    print("🎉 所有集成测试通过!")
    print("✨ 你的电商平台后端运行正常!")
else:
    print("⚠️  部分测试失败，请检查以上错误信息")
    print("💡 提示: 确保已经生成了测试数据")