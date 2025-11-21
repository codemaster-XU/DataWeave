import random
from faker import Faker

fake = Faker('zh_CN')

# 中国省市数据
PROVINCES_CITIES = {
    "北京市": ["北京市"],
    "上海市": ["上海市"],
    "广东省": ["广州市", "深圳市", "东莞市", "佛山市"],
    "浙江省": ["杭州市", "宁波市", "温州市", "绍兴市"],
    "江苏省": ["南京市", "苏州市", "无锡市", "常州市"],
    "四川省": ["成都市", "绵阳市", "德阳市", "宜宾市"],
    "湖北省": ["武汉市", "黄石市", "十堰市", "宜昌市"]
}

CATEGORIES = [
    (1, "Electronics", "电子产品"),
    (2, "Clothing", "服装鞋帽"),
    (3, "Books", "图书文娱"),
    (4, "Home", "家居用品"),
    (5, "Sports", "运动户外")
]

def get_random_location():
    province = random.choice(list(PROVINCES_CITIES.keys()))
    city = random.choice(PROVINCES_CITIES[province])
    return province, city

def get_random_category():
    return random.choice(CATEGORIES)