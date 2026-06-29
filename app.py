from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DB_PATH = "market.db"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            category TEXT,
            location TEXT,
            description TEXT,
            image TEXT,
            phone TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            sender TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("PRAGMA table_info(products)")
    columns = {row[1] for row in c.fetchall()}

    if "category" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN category TEXT")

    if "location" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN location TEXT")

    c.execute("PRAGMA table_info(messages)")
    message_columns = {row[1] for row in c.fetchall()}

    if "product_id" not in message_columns:
        c.execute("ALTER TABLE messages ADD COLUMN product_id INTEGER")

    if "created_at" not in message_columns:
        c.execute("ALTER TABLE messages ADD COLUMN created_at TIMESTAMP")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME + SEARCH ----------------
@app.route("/")
def home():
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    location = request.args.get("location", "")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    query += " ORDER BY id DESC"

    c.execute(query, params)

    products = c.fetchall()

    c.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category
    """)
    categories = [row["category"] for row in c.fetchall()]

    c.execute("""
        SELECT DISTINCT location
        FROM products
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
    """)
    locations = [row["location"] for row in c.fetchall()]

    conn.close()

    return render_template(
        "index.html",
        products=products,
        search=search,
        category=category,
        location=location,
        categories=categories,
        locations=locations
    )

# ---------------- PRODUCT DETAILS ----------------
@app.route("/product/<int:id>")
def product(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    )

    item = c.fetchone()
    conn.close()

    if item:
        return render_template(
            "product.html",
            item=item
        )

    return "Product not found"

# ---------------- CHAT ----------------
@app.route("/chat/<int:product_id>", methods=["GET", "POST"])
def chat(product_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    )
    item = c.fetchone()

    if not item:
        conn.close()
        return "Product not found"

    if request.method == "POST":
        message = request.form["message"]

        c.execute("""
            INSERT INTO messages (product_id, sender, message)
            VALUES (?, ?, ?)
        """, (
            product_id,
            "You",
            message
        ))

        conn.commit()
        conn.close()

        return redirect(f"/chat/{product_id}")

    c.execute("""
        SELECT sender, message
        FROM messages
        WHERE product_id=?
        ORDER BY id ASC
    """, (
        product_id,
    ))
    messages = c.fetchall()
    conn.close()

    return render_template(
        "chat.html",
        item=item,
        seller=item["phone"],
        messages=messages
    )

# ---------------- SERVE IMAGES ----------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

# ---------------- SELL ----------------
@app.route("/sell", methods=["GET", "POST"])
def sell():

    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]
        phone = request.form["phone"]

        image = request.files.get("image")

        filename = ""

        if image and image.filename:
            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            INSERT INTO products
            (name, price, category, location, description, image, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            price,
            category,
            location,
            description,
            filename,
            phone
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("sell.html")

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
