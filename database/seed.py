import random
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.engine import Engine


CATEGORIES = [
    {"id": 1, "name": "Electronics", "parent_id": None},
    {"id": 2, "name": "Computers", "parent_id": 1},
    {"id": 3, "name": "Phones", "parent_id": 1},
    {"id": 4, "name": "Accessories", "parent_id": 1},
    {"id": 5, "name": "Clothing", "parent_id": None},
    {"id": 6, "name": "Men's Wear", "parent_id": 5},
    {"id": 7, "name": "Women's Wear", "parent_id": 5},
    {"id": 8, "name": "Home & Garden", "parent_id": None},
]

PRODUCTS = [
    {"id": 1, "name": "Laptop Pro 15", "category_id": 2, "price": 1299.99, "stock": 25},
    {"id": 2, "name": "Wireless Mouse", "category_id": 4, "price": 29.99, "stock": 150},
    {"id": 3, "name": "Mechanical Keyboard", "category_id": 4, "price": 89.99, "stock": 75},
    {"id": 4, "name": "USB-C Hub", "category_id": 4, "price": 49.99, "stock": 100},
    {"id": 5, "name": "iPhone 15 Pro", "category_id": 3, "price": 999.99, "stock": 30},
    {"id": 6, "name": "Samsung Galaxy S24", "category_id": 3, "price": 849.99, "stock": 40},
    {"id": 7, "name": "Phone Case", "category_id": 4, "price": 19.99, "stock": 200},
    {"id": 8, "name": "Screen Protector", "category_id": 4, "price": 9.99, "stock": 300},
    {"id": 9, "name": "Men's T-Shirt", "category_id": 6, "price": 19.99, "stock": 500},
    {"id": 10, "name": "Men's Jeans", "category_id": 6, "price": 49.99, "stock": 200},
    {"id": 11, "name": "Women's Dress", "category_id": 7, "price": 59.99, "stock": 150},
    {"id": 12, "name": "Women's Blouse", "category_id": 7, "price": 34.99, "stock": 180},
    {"id": 13, "name": "Garden Hose", "category_id": 8, "price": 24.99, "stock": 80},
    {"id": 14, "name": "Plant Pot Set", "category_id": 8, "price": 39.99, "stock": 60},
    {"id": 15, "name": "LED Desk Lamp", "category_id": 8, "price": 34.99, "stock": 90},
]

COUNTRIES = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan", "Brazil"]


def create_tables(engine: Engine) -> None:
    with open("config/schema.sql") as f:
        ddl = f.read()
    with engine.connect() as conn:
        for statement in ddl.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()


def seed_data(engine: Engine) -> None:
    with engine.connect() as conn:
        for table in ["order_items", "orders", "products", "customers", "categories"]:
            conn.execute(text(f"DELETE FROM {table}"))

        for cat in CATEGORIES:
            conn.execute(
                text("INSERT INTO categories (id, name, parent_id) VALUES (:id, :name, :parent_id)"),
                cat,
            )

        for prod in PRODUCTS:
            conn.execute(
                text("INSERT INTO products (id, name, category_id, price, stock_quantity) VALUES (:id, :name, :category_id, :price, :stock)"),
                prod,
            )

        for i in range(1, 51):
            conn.execute(
                text("INSERT INTO customers (id, first_name, last_name, email, country, created_at) VALUES (:id, :first_name, :last_name, :email, :country, :created_at)"),
                {
                    "id": i,
                    "first_name": f"First{i}",
                    "last_name": f"Last{i}",
                    "email": f"user{i}@example.com",
                    "country": random.choice(COUNTRIES),
                    "created_at": datetime.now() - timedelta(days=random.randint(1, 730)),
                },
            )

        order_id = 1
        order_item_id = 1
        statuses = ["pending", "shipped", "delivered", "cancelled"]

        for _ in range(200):
            customer_id = random.randint(1, 50)
            order_date = datetime.now() - timedelta(days=random.randint(1, 365))
            status = random.choices(statuses, weights=[0.1, 0.2, 0.6, 0.1])[0]
            num_items = random.randint(1, 5)
            product_ids = random.sample(range(1, 16), num_items)

            total_amount = 0
            for pid in product_ids:
                result = conn.execute(text("SELECT price FROM products WHERE id = :pid"), {"pid": pid})
                price = result.scalar()
                qty = random.randint(1, 3)
                total_amount += price * qty

            conn.execute(
                text("INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES (:id, :customer_id, :order_date, :status, :total_amount)"),
                {
                    "id": order_id,
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "status": status,
                    "total_amount": round(total_amount, 2),
                },
            )

            for pid in product_ids:
                result = conn.execute(text("SELECT price FROM products WHERE id = :pid"), {"pid": pid})
                price = result.scalar()
                qty = random.randint(1, 3)
                conn.execute(
                    text("INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (:id, :order_id, :product_id, :quantity, :unit_price)"),
                    {
                        "id": order_item_id,
                        "order_id": order_id,
                        "product_id": pid,
                        "quantity": qty,
                        "unit_price": price,
                    },
                )
                order_item_id += 1

            order_id += 1

        conn.commit()
        print("Database seeded successfully!")