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
            teacher_name TEXT,
            department TEXT,
            room TEXT UNIQUE,
            status TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/upload', methods=['GET'])
def upload_data():
    raw = request.args.get('value')
    if raw is None:
        return "Missing 'value' parameter", 400

    parts = raw.split(",")
    if len(parts) != 4:
        return "Invalid value format", 400

    teacher_name, department, room, status = parts

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- ここから追加 ---
    # 同じ部屋のレコードがあるか確認
    c.execute("SELECT id FROM sensor_data WHERE room = ?", (room,))
    row = c.fetchone()

    if row:
        # 更新
        c.execute(
            """
            UPDATE sensor_data
            SET teacher_name = ?, department = ?, status = ?, timestamp = ?
            WHERE room = ?
            """,
            (teacher_name, department, status, datetime.now(), room)
        )
    else:
        # 新規挿入
        c.execute(
            """
            INSERT INTO sensor_data (teacher_name, department, room, status, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (teacher_name, department, room, status, datetime.now())
        )
    # --- 追加ここまで ---

    conn.commit()
    conn.close()
    return "OK", 200


@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT teacher_name, department, room, status, timestamp
        FROM sensor_data
        ORDER BY timestamp DESC
        LIMIT 10
        """
    )
    rows = c.fetchall()
    conn.close()

    return render_template('index.html', data=rows)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
