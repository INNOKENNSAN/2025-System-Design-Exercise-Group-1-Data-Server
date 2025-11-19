from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 変更：カラムを4つに増やす
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT,
            department TEXT,
            room TEXT,
            status TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/upload', methods=['GET'])
def upload_data():
    """
    GET /upload?value=...
    valueの形式:
        教員名,学科,部屋,対応状況
    例:
        山田太郎,情報工学科,3号館402,応対可能
    """

    raw = request.args.get('value')
    if raw is None:
        return "Missing 'value' parameter", 400

    # 受信データを分解
    parts = raw.split(",")
    if len(parts) != 4:
        return "Invalid value format", 400

    teacher_name, department, room, status = parts

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO sensor_data (teacher_name, department, room, status, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (teacher_name, department, room, status, datetime.now())
    )

    conn.commit()
    conn.close()
    return "OK", 200


@app.route('/')
def index():
    """
    センサデータを新しい順に10件まで表示
    """
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