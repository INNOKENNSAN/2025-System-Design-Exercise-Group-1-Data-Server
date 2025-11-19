from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # room に UNIQUE を付けることで同じ部屋の重複登録を防ぐ
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
    """
    GET /upload?value=...
    value の形式:
        教員名,学科,部屋,対応状況
    """

    raw = request.args.get('value')
    if raw is None:
        return "Missing 'value' parameter", 400

    # 受信データを分割
    parts = raw.split(",")
    if len(parts) != 4:
        return "Invalid value format", 400

    teacher_name, department, room, status = parts

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 同じ部屋(room)のデータがあるか確認
    c.execute("SELECT id FROM sensor_data WHERE room = ?", (room,))
    row = c.fetchone()

    if row:
        # UPDATE（上書き）
        c.execute(
            """
            UPDATE sensor_data
            SET teacher_name = ?, department = ?, status = ?, timestamp = ?
            WHERE room = ?
            """,
            (teacher_name, department, status, datetime.now(), room)
        )
    else:
        # INSERT（新規）
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
    データを学科名順（department ASC）で表示
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # department 昇順 → timestamp 降順 で並べる
    c.execute(
        """
        SELECT teacher_name, department, room, status, timestamp
        FROM sensor_data
        ORDER BY department ASC, timestamp DESC
        """
    )

    rows = c.fetchall()
    conn.close()

    # index.html の {{ now }} に渡す
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template('index.html', data=rows, now=now_str)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
