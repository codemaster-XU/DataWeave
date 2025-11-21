# services/api.py
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, jsonify, request
from flask_cors import CORS
from database.session import OLTPSession
from sqlalchemy import text

app = Flask(__name__)
CORS(app)  # 允许跨域请求

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Ecommerce Backend API"})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    session = OLTPSession()
    try:
        # 先检查 users 表是否有 email 列
        result = session.execute(
            text("PRAGMA table_info(users)")
        )
        columns = [row[1] for row in result]
        has_email = 'email' in columns
        
        if has_email:
            query = text("SELECT user_id, username, email, registration_date, province, city FROM users WHERE user_id = :user_id")
        else:
            query = text("SELECT user_id, username, registration_date, province, city FROM users WHERE user_id = :user_id")
        
        result = session.execute(query, {'user_id': user_id})
        user = result.fetchone()
        
        if user:
            if has_email:
                return jsonify({
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'registration_date': user[3].isoformat() if user[3] else None,
                    'province': user[4],
                    'city': user[5]
                })
            else:
                return jsonify({
                    'user_id': user[0],
                    'username': user[1],
                    'registration_date': user[2].isoformat() if user[2] else None,
                    'province': user[3],
                    'city': user[4]
                })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    session = OLTPSession()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # 检查表结构
        result = session.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        has_email = 'email' in columns
        
        if has_email:
            query = text("""
                SELECT user_id, username, email, registration_date, province, city 
                FROM users 
                ORDER BY user_id 
                LIMIT :limit OFFSET :offset
            """)
        else:
            query = text("""
                SELECT user_id, username, registration_date, province, city 
                FROM users 
                ORDER BY user_id 
                LIMIT :limit OFFSET :offset
            """)
        
        result = session.execute(query, {'limit': per_page, 'offset': offset})
        users = []
        
        for row in result:
            if has_email:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'registration_date': row[3].isoformat() if row[3] else None,
                    'province': row[4],
                    'city': row[5]
                })
            else:
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'registration_date': row[2].isoformat() if row[2] else None,
                    'province': row[3],
                    'city': row[4]
                })
        
        # 获取总数
        count_result = session.execute(text("SELECT COUNT(*) FROM users"))
        total = count_result.scalar()
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/products/top-selling', methods=['GET'])
def get_top_selling_products():
    session = OLTPSession()
    try:
        result = session.execute(
            text("""
                SELECT p.product_id, p.product_name, p.category_name, p.price,
                       SUM(oi.quantity) as total_sold
                FROM products p
                JOIN order_items oi ON p.product_id = oi.product_id
                GROUP BY p.product_id, p.product_name, p.category_name, p.price
                ORDER BY total_sold DESC
                LIMIT 10
            """)
        )
        
        products = []
        for row in result:
            products.append({
                'product_id': row[0],
                'product_name': row[1],
                'category_name': row[2],
                'price': float(row[3]) if row[3] else 0,
                'total_sold': row[4] or 0
            })
        
        return jsonify(products)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """获取仪表板统计信息"""
    session = OLTPSession()
    try:
        # 用户总数
        user_result = session.execute(text("SELECT COUNT(*) FROM users"))
        total_users = user_result.scalar()
        
        # 商品总数
        product_result = session.execute(text("SELECT COUNT(*) FROM products"))
        total_products = product_result.scalar()
        
        # 订单总数
        order_result = session.execute(text("SELECT COUNT(*) FROM orders"))
        total_orders = order_result.scalar()
        
        # 总销售额
        sales_result = session.execute(text("SELECT SUM(total_amount) FROM orders"))
        total_sales = sales_result.scalar() or 0
        
        return jsonify({
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_sales': float(total_sales)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    print("🚀 启动电商数据 API 服务...")
    print(f"📁 项目根目录: {project_root}")
    app.run(debug=True, host='0.0.0.0', port=5000)