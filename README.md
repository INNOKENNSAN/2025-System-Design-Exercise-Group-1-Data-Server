# 2025--1-


〇ファイル構成(予定)
sensei-switch/
├─ app/
│  ├─ logs
│  │  ├─ format_error.log
│  │  ├─ unregistered_id.log
│  │  └─status_change.log
│  ├─ main.py
│  ├─ handlers_status.py
│  ├─ api_admin_logic.py
│  ├─ db.py
│  ├─ utils_log.py
│  ├─ migrations/
│  │   └─ init_db.py
│  └─ templates/
│       ├─ admin.html
│       ├─ view.html
│       ├─ css/
│       │  └─ style.css
│       └─ js/
│          ├─ admin.js
│          └─ view.js
├─ .gitignore
├─ Dockerfile
├─ docker-compose.yml
├─ entrypoint.sh
└─ README.md


〇閲覧用ページでAPIが投げるデータ形式
[
  {
    "name": "山田太郎",
    "department": "情報工学科",
    "grade": "3",
    "role": "教授",
    "room": "A101",
    "status": "在室"
  }
]

〇対応状況テスト用
・単体（可）
http://localhost:5000/api/status_update?data=1,1
・単体（不可）
http://localhost:5000/api/status_update?data=1,0
・複数人（可、不可、可）
http://localhost:5000/api/status_update?data=1,1,2,0,3,1
・未登録ID
http://localhost:5000/api/status_update?data=1,1,999,0
・フォーマットエラー
http://localhost:5000/api/status_update?data=1,1,2
・ステータス不正値
http://localhost:5000/api/status_update?data=1,2



・追加API
http://localhost:5000/api/admin?action=add&name=佐藤&department=理科&grade=2&role=副担任&room=202
・削除API
http://localhost:5000/api/admin?action=delete&person_id=4