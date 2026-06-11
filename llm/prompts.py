from config.settings import settings
from llm.schema_context import get_schema_context

SYSTEM_PROMPT = """You are a SQL expert. Generate ONLY a SQL query. No explanations, no markdown, no extra text.

Rules:
1. Only SELECT statements - never INSERT, UPDATE, DELETE, DROP, CREATE, ALTER
2. Always include a LIMIT clause (default: 1000)
3. Use proper JOINs based on foreign key relationships
4. Use GROUP BY, HAVING, ORDER BY when needed
5. Output the SQL inside ```sql ... ``` code block
6. If ambiguous, choose the most reasonable interpretation
7. Use strftime() for date operations on SQLite
8. Use COALESCE() for NULL handling"""

FEW_SHOTS = [
    {
        "question": "Show all products in the Electronics category",
        "sql": "SELECT p.name, p.price FROM products p JOIN categories c ON p.category_id = c.id WHERE c.name = 'Electronics';"
    },
    {
        "question": "What's the total revenue by country?",
        "sql": "SELECT c.country, SUM(o.total_amount) as total_revenue FROM orders o JOIN customers c ON o.customer_id = c.id GROUP BY c.country ORDER BY total_revenue DESC;"
    },
    {
        "question": "List customers who ordered more than 3 times",
        "sql": "SELECT c.first_name, c.last_name, c.email, COUNT(o.id) as order_count FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id HAVING COUNT(o.id) > 3;"
    },
    {
        "question": "Show orders with product names and quantities",
        "sql": "SELECT o.id, o.order_date, p.name as product_name, oi.quantity, oi.unit_price FROM orders o JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id ORDER BY o.order_date DESC LIMIT 10;"
    },
    {
        "question": "Find products priced above the average",
        "sql": "SELECT name, price FROM products WHERE price > (SELECT AVG(price) FROM products);"
    },
    {
        "question": "Monthly order count for 2024",
        "sql": "SELECT strftime('%Y-%m', order_date) as month, COUNT(*) as orders FROM orders WHERE strftime('%Y', order_date) = '2024' GROUP BY month ORDER BY month;"
    },
    {
        "question": "Top 5 customers by lifetime value with their favorite category",
        "sql": "WITH customer_ltv AS (SELECT c.id, c.first_name, c.last_name, SUM(o.total_amount) as ltv FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id), fav_cat AS (SELECT c.id, cat.name as fav_category FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id JOIN categories cat ON p.category_id = cat.id GROUP BY c.id, cat.name ORDER BY COUNT(*) DESC) SELECT cltv.first_name, cltv.last_name, cltv.ltv, fc.fav_category FROM customer_ltv cltv JOIN fav_cat fc ON cltv.id = fc.id ORDER BY cltv.ltv DESC LIMIT 5;"
    },
    {
        "question": "Which categories have no products in stock?",
        "sql": "SELECT c.name FROM categories c WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.category_id = c.id AND p.stock_quantity > 0);"
    },
    {
        "question": "Show all categories with their parent category name",
        "sql": "SELECT c1.name as category, c2.name as parent_category FROM categories c1 LEFT JOIN categories c2 ON c1.parent_id = c2.id;"
    },
]


def build_prompt(question: str, schema_context: str | None = None) -> str:
    if schema_context is None:
        schema_context = get_schema_context()

    parts = [SYSTEM_PROMPT]
    parts.append(f"\nDatabase Schema:\n{schema_context}")
    parts.append("\nExamples:")

    for i, shot in enumerate(FEW_SHOTS[:settings.few_shot_count], 1):
        parts.append(f"\nExample {i}:")
        parts.append(f"Q: {shot['question']}")
        parts.append(f"```sql\n{shot['sql']}\n```")

    parts.append(f"\nNow answer this question. Output ONLY the SQL inside ```sql ... ```:")
    parts.append(f"Q: {question}")
    parts.append("```sql")

    return "\n".join(parts)