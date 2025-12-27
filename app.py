import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ================= CLOUDINARY CONFIG =================
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET")
)

# ================= CONFIG =================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
DB_NAME = "art_gallery.db"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            public_id TEXT NOT NULL,
            name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= ROUTES =================
@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, image_url, name FROM photos ORDER BY id DESC")
    photos = c.fetchall()
    conn.close()
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    files = request.files.getlist('file')
    user_name = request.form.get('photo_name', '')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for file in files:
        if file and allowed_file(file.filename):
            public_id = str(uuid.uuid4())

            result = cloudinary.uploader.upload(
                file,
                folder="kalakendra",
                public_id=public_id
            )

            c.execute(
                "INSERT INTO photos (image_url, public_id, name) VALUES (?, ?, ?)",
                (result["secure_url"], public_id, user_name)
            )

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT public_id FROM photos WHERE id = ?", (photo_id,))
    result = c.fetchone()

    if result:
        cloudinary.uploader.destroy(f"kalakendra/{result[0]}")
        c.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()

    conn.close()
    return jsonify({"status": "success"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
