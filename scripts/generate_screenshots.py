"""Generate realistic demo screenshots for the README using PIL."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from pipeline.executor import execute_safe, to_markdown
from guardrails.sql_validator import validator


def _get_font(size=14):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, fill, radius=8, outline=None):
    if fill == "transparent":
        return
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def _draw_ui_frame(draw, w, h, title="Text-to-SQL Guardrails"):
    sidebar_w = 220
    _draw_rounded_rect(draw, (0, 0, w, h), fill="#0E1117")
    _draw_rounded_rect(draw, (0, 0, sidebar_w, h), fill="#1A1D24")
    _draw_rounded_rect(draw, (sidebar_w, 0, w, 50), fill="#1A1D24")

    draw.text((sidebar_w + 16, 14), title, fill="#FFFFFF",
              font=_get_font(18))

    nav_items = ["Chat", "Schema Viewer", "Guardrails Config"]
    for i, item in enumerate(nav_items):
        y = 80 + i * 40
        is_active = item == "Chat"
        bg = "#262A35" if is_active else "transparent"
        _draw_rounded_rect(draw, (10, y, sidebar_w - 10, y + 32),
                           fill=bg, radius=6)
        draw.text((24, y + 6), item, fill="#FFFFFF" if is_active else "#8A8D98",
                  font=_get_font(14))


def generate_query_result():
    sql = ("SELECT c.first_name, c.last_name, c.email, "
           "COUNT(o.id) as order_count, SUM(o.total_amount) as total_spent "
           "FROM customers c JOIN orders o ON c.id = o.customer_id "
           "GROUP BY c.id ORDER BY total_spent DESC LIMIT 5")
    df = execute_safe(sql)
    table_text = to_markdown(df)

    val = validator.validate(sql)
    guardrail_status = "PASSED" if val.valid else "BLOCKED"

    w, h = 1000, 640
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    _draw_ui_frame(draw, w, h)

    font = _get_font(12)
    small_font = _get_font(11)
    mono_font = _get_font(11)

    x0 = 240
    y = 70
    draw.text((x0, y), "Ask a question about your database:",
              fill="#CCCCCC", font=font)
    _draw_rounded_rect(draw, (x0, y + 24, w - 24, y + 54),
                       fill="#262A35", radius=6)
    draw.text((x0 + 10, y + 31), "Top 5 customers by revenue",
              fill="#AAAAAA", font=small_font)

    y = 110
    draw.text((x0, y), "Generated SQL:", fill="#CCCCCC", font=font)
    lines = sql.split(" ")
    sql_display = ""
    current_line = ""
    for word in lines:
        test = current_line + " " + word if current_line else word
        if len(test) > 75:
            sql_display += current_line + "\n"
            current_line = word
        else:
            current_line = test
    sql_display += current_line
    _draw_rounded_rect(draw, (x0, y + 20, w - 24, y + 110),
                       fill="#1E1E1E", radius=6)
    draw.text((x0 + 8, y + 26), sql_display, fill="#D4D4D4", font=mono_font)

    y = 155
    guardrail_color = "#2ECC71" if val.valid else "#E74C3C"
    _draw_rounded_rect(draw, (x0, y + 110, x0 + 140, y + 134),
                       fill=guardrail_color, radius=4)
    draw.text((x0 + 12, y + 114), f"Guardrails: {guardrail_status}",
              fill="#FFFFFF", font=small_font)

    y2 = 290
    draw.text((x0, y2), "Results:", fill="#CCCCCC", font=font)
    _draw_rounded_rect(draw, (x0, y2 + 20, w - 24, h - 20),
                       fill="#1A1D24", radius=6)

    table_lines = table_text.split("\n")
    for i, line in enumerate(table_lines):
        color = "#8A8D98" if i == 1 else "#D4D4D4"
        draw.text((x0 + 12, y2 + 28 + i * 20), line,
                  fill=color, font=mono_font)
        if i == 0:
            draw.line(
                (x0 + 12, y2 + 48 + i * 20, w - 36, y2 + 48 + i * 20),
                fill="#333333", width=1)

    img.save("docs/screenshots/query_result.png")
    print("Created docs/screenshots/query_result.png")


def generate_blocked_query():
    sql = "DROP TABLE orders; SELECT * FROM products"
    val = validator.validate(sql)

    w, h = 1000, 640
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    _draw_ui_frame(draw, w, h)
    font = _get_font(12)
    small_font = _get_font(11)
    mono_font = _get_font(11)
    x0 = 240
    y = 70
    draw.text((x0, y), "Ask a question about your database:",
              fill="#CCCCCC", font=font)
    _draw_rounded_rect(draw, (x0, y + 24, w - 24, y + 54),
                       fill="#262A35", radius=6)
    draw.text((x0 + 10, y + 31), "Delete all orders from the database",
              fill="#AAAAAA", font=small_font)

    y = 110
    draw.text((x0, y), "Generated SQL:", fill="#CCCCCC", font=font)
    _draw_rounded_rect(draw, (x0, y + 20, w - 24, y + 56),
                       fill="#1E1E1E", radius=6)
    draw.text((x0 + 8, y + 26), "DROP TABLE orders;\nSELECT * FROM products;",
              fill="#D4D4D4", font=mono_font)

    guardrail_color = "#E74C3C"
    _draw_rounded_rect(draw, (x0, y + 61, x0 + 155, y + 85),
                       fill=guardrail_color, radius=4)
    draw.text((x0 + 12, y + 65), "Guardrails: BLOCKED",
              fill="#FFFFFF", font=small_font)

    y2 = 190
    _draw_rounded_rect(draw, (x0, y2, w - 24, h - 20),
                       fill="#1A1D24", radius=6)

    error_msgs = [
        "Destructive statement blocked: DROP",
        "Read-only violations blocked: DML detected (DELETE, DROP, INSERT, UPDATE)",
        "Multi-statement queries not allowed",
    ]
    for i, msg in enumerate(error_msgs):
        y_pos = y2 + 20 + i * 28
        _draw_rounded_rect(draw, (x0 + 12, y_pos, x0 + 40, y_pos + 20),
                           fill="#E74C3C", radius=4)
        draw.text((x0 + 18, y_pos + 2), "✗", fill="#FFFFFF", font=small_font)
        draw.text((x0 + 48, y_pos + 2), msg, fill="#FF6B6B", font=mono_font)

    y_warn = y2 + 120
    draw.text((x0 + 16, y_warn), "Warnings:", fill="#CCCCCC", font=font)
    warn_msgs = [
        "No LIMIT clause found - results may be large",
    ]
    for i, msg in enumerate(warn_msgs):
        y_pos = y_warn + 24 + i * 28
        _draw_rounded_rect(draw, (x0 + 12, y_pos, x0 + 40, y_pos + 20),
                           fill="#F39C12", radius=4)
        draw.text((x0 + 18, y_pos + 2), "!", fill="#FFFFFF", font=small_font)
        draw.text((x0 + 48, y_pos + 2), msg, fill="#F5B041", font=mono_font)

    img.save("docs/screenshots/blocked_query.png")
    print("Created docs/screenshots/blocked_query.png")


if __name__ == "__main__":
    generate_query_result()
    generate_blocked_query()
