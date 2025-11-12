from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/upload', methods=['GET'])
def upload_data():
    value = request.args.get('value')
    if value is None:
        return "Missing 'value' parameter", 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (value, timestamp) VALUES (?, ?)", (value, datetime.now()))
    conn.commit()
    conn.close()
    return "OK", 200

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value, timestamp FROM sensor_data ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('index.html', data=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
