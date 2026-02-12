from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import jwt
import os
import logging

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
DB_HOST = os.getenv('DB_HOST', 'postgres-product')
DB_NAME = os.getenv('DB_NAME', 'productdb')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample data
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            sample_products = [
                ('Laptop', 'High-performance laptop', 999.99, 10),
                ('Mouse', 'Wireless mouse', 29.99, 50),
                ('Keyboard', 'Mechanical keyboard', 79.99, 30),
                ('Monitor', '27-inch 4K monitor', 399.99, 15),
                ('Headphones', 'Noise-canceling headphones', 199.99, 25)
            ]
            cur.executemany(
                "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)",
                sample_products
            )
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Product database initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "product-service"}), 200

@app.route('/api/products', methods=['GET'])
def list_products():
    """List all products - PUBLIC endpoint"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, price, stock FROM products")
        products = []
        for row in cur.fetchall():
            products.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': float(row[3]),
                'stock': row[4]
            })
        cur.close()
        conn.close()
        return jsonify(products), 200
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details - PUBLIC endpoint"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description, price, stock FROM products WHERE id = %s",
            (product_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "Product not found"}), 404
        
        product = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': float(row[3]),
            'stock': row[4]
        }
        return jsonify(product), 200
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({"error": "Failed to fetch product"}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create product - PROTECTED endpoint"""
    # Verify JWT token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not verify_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        price = data.get('price')
        stock = data.get('stock', 0)
        
        if not name or not price:
            return jsonify({"error": "Name and price required"}), 400
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, description, price, stock)
        )
        product_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Product created: {name}")
        return jsonify({"message": "Product created", "id": product_id}), 201
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({"error": "Failed to create product"}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 8002))
    app.run(host='0.0.0.0', port=port, debug=False)
