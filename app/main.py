# main.py
# エントリポイント (Dockerfile の CMD ["python", "main.py"] に一致)
# Flask を templates/ を static としても使う最小変更方針で初期化し、
# 設計仕様書（4.5節）に準拠したルーティングを提供する。
#
# URL:
#  - 管理画面 (HTML):   /admin/
#  - 閲覧画面 (HTML):   /view/
#  - 受信 API:          /api/status_update?data=<payload>
#  - 管理 API:          /api/admin?action=<list|add|delete|update>&...
#  - 閲覧 API:          /api/status_view
#
# 注意:
#  - 実際のビジネスロジック（パース・DB 更新・ログ出力）は handlers_status.py 等に委譲する。
#  - このファイルは「ルーティングと入力検証」を担う薄いハンドラです。

from flask import Flask, request, jsonify, make_response, render_template
from typing import Any
import json
import urllib.parse
import logging
import api_admin_logic

# 別ファイルに実装するモジュールを import（同一ディレクトリ app/ に存在する前提）
try:
    import handlers_status
except Exception as e:
    logging.warning("handlers_status import failed: %s", e)
    handlers_status = None

try:
    import api_admin_logic
except Exception as e:
    logging.warning("api_admin_logic import failed: %s", e)
    api_admin_logic = None

try:
    import db
except Exception as e:
    logging.warning("db import failed: %s", e)
    db = None

try:
    import utils_log
except Exception as e:
    logging.warning("utils_log import failed: %s", e)
    utils_log = None


# Flask の初期化:
# - static_folder と template_folder を両方 "templates" にして
#   /static/* の URL で templates 内の css/js を提供する（最小変更方針）。
app = Flask(
    __name__,
    static_folder="templates",   # 静的ファイルは templates/ 以下を参照
    static_url_path="/static",   # ブラウザ側 URL は /static/...
    template_folder="templates"  # render_template() に templates/ を使う
)

# 起動時にログディレクトリを確保（存在チェック）。utils_log に委譲。
if utils_log is not None and hasattr(utils_log, "ensure_log_dir_exists"):
    try:
        utils_log.ensure_log_dir_exists()
    except Exception as e:
        logging.warning("ログディレクトリの初期化に失敗しました: %s", e)


# ユーティリティ: JSON レスポンス作成
def json_response(body: Any, status: int = 200):
    resp = make_response(jsonify(body), status)
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


# -----------------------
# 受信 API: /api/status_update
# -----------------------
@app.route("/api/status_update", methods=["GET"])
def api_status_update():
    """
    端末からのステータス更新を受け付ける。
    クエリ: ?data=<payload> で payload は "ID,STATUS,ID,STATUS,..." のカンマ区切り。
    実処理は handlers_status.handle_status_update_request に委譲。
    """
    raw_data = request.args.get("data")
    if raw_data is None:
        return json_response({"result": "error", "reason": "missing_data"}, 400)

    if handlers_status is None or not hasattr(handlers_status, "handle_status_update_request"):
        return json_response({"result": "error", "reason": "server_not_ready", "detail": "handlers_status missing"}, 500)

    try:
        # handlers_status は (http_status:int, response_dict:dict) を返す想定
        http_status, resp = handlers_status.handle_status_update_request(raw_data)
        return json_response(resp, http_status)
    except Exception as e:
        logging.exception("handle_status_update_request 実行中に例外が発生しました")
        return json_response({"result": "error", "reason": "internal_error", "detail": str(e)}, 500)


# -----------------------
# 管理 API: /api/admin?action=...
# -----------------------
@app.route("/api/admin", methods=["GET"])
def api_admin():
    try:
        action = request.args.get("action")

        if action == "list":
            result = api_admin_logic.get_people_list()
            return json_response(result, 200)

        elif action == "bulk_update":
            records_json = request.args.get("records")
            if not records_json:
                return json_response(
                    {"result": "error", "reason": "missing_records"},
                    400
                )

            records = json.loads(records_json)
            detail = api_admin_logic.apply_bulk_updates(records)
            return json_response(
                {"result": "ok", "detail": detail},
                200
            )

        elif action == "add":
            default_data = {
                "name": request.args.get("name"),
                "department": request.args.get("department"),
                "grade": request.args.get("grade"),
                "role": request.args.get("role"),
                "room": request.args.get("room"),
            }
            new_id = api_admin_logic.insert_person(default_data)
            return json_response(
                {"result": "ok", "id": new_id},
                200
            )

        elif action == "delete":
            person_id = request.args.get("person_id")
            if not person_id:
                return json_response(
                    {"result": "error", "reason": "missing_person_id"},
                    400
                )

            api_admin_logic.delete_person(int(person_id))
            return json_response({"result": "ok"}, 200)

        else:
            return json_response(
                {"result": "error", "reason": "unknown_action"},
                400
            )

    except api_admin_logic.ApiError as ae:
        return json_response(
            {
                "result": "error",
                "reason": ae.reason,
                "message": str(ae),
            },
            ae.status_code,
        )

    except Exception:
        logging.exception("admin api unexpected error")
        return json_response(
            {"result": "error", "reason": "internal_error"},
            500
        )



# -----------------------
# 閲覧用 API: /api/status_view
# -----------------------
@app.route("/api/status_view", methods=["GET"])
def api_status_view():
    """
    閲覧用一覧を返す。db.get_status_table() に委譲。
    返却形式: { result: "ok", records: [...] }
    """
    if db is None or not hasattr(db, "get_status_table"):
        return json_response({"result": "error", "reason": "server_not_ready", "detail": "db missing"}, 500)

    try:
        records = db.get_status_table()
        return json_response({"result": "ok", "records": records}, 200)
    except Exception as e:
        logging.exception("db.get_status_table 実行中に例外が発生しました")
        return json_response({"result": "error", "reason": "internal_error", "detail": str(e)}, 500)


# -----------------------
# 管理画面 / 閲覧画面 (HTML)
# -----------------------
@app.route("/admin/", methods=["GET"])
def serve_admin_page():
    """
    templates/admin.html をレンダリングして返す。
    CSS/JS は /static/... の URL で参照する想定（templates 配下の css/js を /static/* で提供）。
    """
    try:
        return render_template("admin.html")
    except Exception as e:
        logging.exception("管理画面のレンダリングに失敗しました")
        return json_response({"result": "error", "reason": "file_not_found", "detail": str(e)}, 500)


@app.route("/view/", methods=["GET"])
def serve_view_page():
    """
    templates/view.html をレンダリングして返す。
    """
    try:
        return render_template("view.html")
    except Exception as e:
        logging.exception("閲覧画面のレンダリングに失敗しました")
        return json_response({"result": "error", "reason": "file_not_found", "detail": str(e)}, 500)


# -----------------------
# アプリ起動
# -----------------------
if __name__ == "__main__":
    # コンテナ実行向けの設定: host=0.0.0.0, port=5000, debug=False
    # 開発時は debug=True にして動作確認してください。
    app.run(host="0.0.0.0", port=5000, debug=False)
