# database.py में जोड़ें

import sqlite3
from datetime import datetime

# अपने मौजूदा create_tables function के अंदर इसे जोड़ें:
def create_tables():
    conn = sqlite3.connect('scores.db') # आपका मौजूदा DB नाम
    cursor = conn.cursor()
    # ... (आपका पुराना कोड) ...
    
    # नया Table Files के लिए
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            file_id TEXT,
            uploader_id INTEGER,
            upload_date TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# नए Functions File Database के लिए
def save_file(name, file_id, uploader_id):
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO shared_files (name, file_id, uploader_id, upload_date) VALUES (?, ?, ?, ?)",
            (name.lower(), file_id, uploader_id, datetime.now())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # अगर नाम पहले से मौजूद है
    finally:
        conn.close()

def get_file_by_name(name):
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM shared_files WHERE name = ?", (name.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_files():
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM shared_files ORDER BY name ASC")
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]
