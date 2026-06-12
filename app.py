from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("market.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            description TEXT,
            image TEXT,
            phone TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    conn = sqlite3.connect("market.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    conn.close()

    return render_template("index.html", products=products)

# ---------------- SERVE IMAGES ----------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------- SELL ----------------
@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]
        desc = request.form["desc"]
        phone = request.form["phone"]

        image = request.files["image"]

        filename = ""

        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("market.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO products
            (name, price, description, image, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (name, price, desc, filename, phone))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("sell.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
