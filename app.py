import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION CHANGES ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 1. FIX 413 ERROR (Allow up to 16GB uploads for 1700+ images)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024 

DB_NAME = "art_gallery.db"

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Setup
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Fetch newest first
    c.execute("SELECT id, filename, name FROM photos ORDER BY id DESC")
    photos = c.fetchall()
    conn.close()
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload_file():
    # 2. FIX MULTIPLE UPLOAD (Handle list of files instead of just one)
    if 'file' not in request.files:
        return redirect(request.url)
    
    # Retrieve multiple files using getlist()
    files = request.files.getlist('file')
    user_name = request.form.get('photo_name', '') # Optional Name applied to batch

    if not files or files[0].filename == '':
        return redirect(request.url)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Loop through every selected image (e.g., all 1700)
    for file in files:
        if file and allowed_file(file.filename):
            # Create unique filename to prevent overwriting
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = str(uuid.uuid4()) + "." + ext
            secure_name = secure_filename(unique_filename)
            
            # Save File to Disk
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_name))
            
            # Save metadata to DB
            c.execute("INSERT INTO photos (filename, name) VALUES (?, ?)", (secure_name, user_name))
            
    conn.commit()
    conn.close()
        
    return redirect(url_for('index'))

@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get filename to delete from disk
    c.execute("SELECT filename FROM photos WHERE id = ?", (photo_id,))
    result = c.fetchone()
    
    if result:
        filename = result[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Delete from Disk
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete from DB
        c.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()
        
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)