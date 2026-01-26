# handlers_status.py
# 端末からのステータス更新データを処理するモジュール
# 設計仕様書 4.5 節に基づき、受信データの解析・DB 更新・ログ出力を行う。
#
# 提供関数:
# - parse_status_payload(raw_data: str) -> List[Tuple[str, str]]
# - write_format_error_log(raw_data: str) -> None
# - write_unregistered_id_log(person_id_raw: str, raw_data: str) -> None
# - write_status_change_log(person_id: int, old_status: int, new_status: int, timestamp: str) -> None
# - handle_status_update_request(raw_data: str) -> Tuple[int, dict]
#
# 前提:
# - utils_log に get_current_timestamp(), write_log_line() が実装されていること
# - db に person_exists(person_id:int) と update_status(person_id:int, status:int, timestamp:str) が実装されていること

from typing import List, Tuple, Optional
import utils_log
import db
import logging
import re



# ★ モジュールロード時に一度だけ保証
try:
    utils_log.ensure_log_dir_exists()
except Exception:
    logging.exception("log directory initialization failed")

# ログファイル名（設計仕様書の規定に準拠）
FORMAT_ERROR_LOG = "format_error.log"
UNREGISTERED_ID_LOG = "unregistered_id.log"
STATUS_CHANGE_LOG = "status_change.log"


# -------------------------------------------------------------
# 1) データ解析（設計 4.5.9.1.6）
# -------------------------------------------------------------
def parse_status_payload(raw_data: str) -> List[Tuple[str, str]]:
    """
    raw_data を解析して [(person_id_raw, status_raw), ...] を返す。
    - raw_data はカンマ区切りのトークン列 "ID,STATUS,ID,STATUS,..."
    - トークン数が奇数の場合は ValueError を投げる（フォーマットエラー）
    - ここでは文字列のまま返し、数値変換は上位で行う（変換失敗で未登録扱いやログを出すため）
    """
    if raw_data is None:
        raise ValueError("raw_data is None")

    parts = re.split(r"[,\s]+", raw_data.strip())
    if len(parts) == 0:
        # 空文字列はフォーマットエラー扱い
        raise ValueError("empty payload")

    if len(parts) % 2 != 0:
        # トークン数が奇数 -> フォーマットエラー
        raise ValueError("invalid payload format: odd number of tokens")

    result: List[Tuple[str, str]] = []
    for i in range(0, len(parts), 2):
        pid_raw = parts[i]
        status_raw = parts[i + 1]
        result.append((pid_raw, status_raw))

    return result


# -------------------------------------------------------------
# 2) フォーマットエラーログ（設計 4.5.9.1.4）
# -------------------------------------------------------------
def write_format_error_log(raw_data: str) -> None:
    """
    フォーマットエラーをログに残す。
    ログ形式: "<timestamp> FORMAT_ERROR <raw_data>"
    """
    try:
        ts = utils_log.get_current_timestamp()
    except Exception:
        # utils_log が未実装/例外なら Python の logging に fallback
        logging.exception("utils_log.get_current_timestamp() failed")
        ts = "UNKNOWN_TIME"

    line = f"{ts} FORMAT_ERROR {raw_data}"
    try:
        utils_log.write_log_line(FORMAT_ERROR_LOG, line)
    except Exception:
        logging.exception("write_log_line failed for format error")


# -------------------------------------------------------------
# 3) 未登録 ID ログ（設計 4.5.9.1.5）
# -------------------------------------------------------------
def write_unregistered_id_log(person_id_raw: str, raw_data: str) -> None:
    """
    未登録 ID を受信した場合にログを残す。
    ログ形式: "<timestamp> UNREGISTERED_ID <person_id_raw> payload=<raw_data>"
    """
    try:
        ts = utils_log.get_current_timestamp()
    except Exception:
        logging.exception("utils_log.get_current_timestamp() failed")
        ts = "UNKNOWN_TIME"

    line = f"{ts} UNREGISTERED_ID {person_id_raw} payload={raw_data}"
    try:
        utils_log.write_log_line(UNREGISTERED_ID_LOG, line)
    except Exception:
        logging.exception("write_log_line failed for unregistered id")


# -------------------------------------------------------------
# 4) 状態変更ログ（設計 4.5.6.2）
# -------------------------------------------------------------
def write_status_change_log(person_id: int, old_status: int, new_status: int, timestamp: str) -> None:
    """
    状態が変化した場合にログを記録する。
    ログ形式: "<timestamp> STATUS_CHANGE id=<person_id> old=<old_status> new=<new_status>"
    """
    line = f"{timestamp} STATUS_CHANGE id={person_id} old={old_status} new={new_status}"
    try:
        utils_log.write_log_line(STATUS_CHANGE_LOG, line)
    except Exception:
        logging.exception("write_log_line failed for status change")


# -------------------------------------------------------------
# 5) メイン処理（設計 4.5.3.3）
# -------------------------------------------------------------
def handle_status_update_request(raw_data: str) -> Tuple[int, dict]:
    """
    端末からのステータス更新リクエストを処理する。
    戻り値: (http_status_code, response_dict)

    フロー（設計に準拠）:
      1) parse_status_payload で形式チェック。ValueError -> フォーマットエラーログ -> 400 を返す。
      2) 各 (person_id_raw, status_raw) ペアを処理:
         - person_id_raw を int に変換できなければ未登録ログを残してスキップ
         - status_raw が "0" or "1" でない場合はフォーマットエラー（400）
         - db.person_exists(person_id) が False の場合は未登録ログを残してスキップ
         - db.update_status(person_id, status_int, timestamp) を呼び、old_status を取得
         - old_status が None（初回挿入）の場合は状態変更ログは出さない
         - old_status が存在し、old_status != new_status の場合は状態変更ログを出す
      3) すべて正常に処理したら 200 + {"result":"ok"} を返す
    """
    # 1) 解析
    try:
        parsed = parse_status_payload(raw_data)
    except ValueError as ve:
        # フォーマットエラー: ログ書き込みして 400 を返す
        write_format_error_log(raw_data)
        return 400, {"result": "error", "reason": "format_error", "detail": str(ve)}

    # 2) 各ペアの処理
    for pid_raw, status_raw in parsed:
        # person_id の整数化
        try:
            person_id = int(pid_raw)
        except Exception:
            # 数値でない -> 未登録ログ（設計では未登録IDはログを残してスキップ）
            write_unregistered_id_log(pid_raw, raw_data)
            continue

        # status の検証（"0" または "1" のみ許可）
        if status_raw not in ("0", "1"):
            # 設計に従いフォーマットエラーとして扱う
            write_format_error_log(raw_data)
            return 400, {"result": "error", "reason": "invalid_status", "detail": status_raw}

        status_int = int(status_raw)

        # DB に登録があるか確認
        try:
            exists = db.person_exists(person_id)
        except Exception:
            logging.exception("db.person_exists failed for id=%s", person_id)
            # DB エラーは内部エラーとして扱う（500）
            return 500, {"result": "error", "reason": "db_error", "detail": "person_exists failed"}

        if not exists:
            write_unregistered_id_log(pid_raw, raw_data)
            continue

        # タイムスタンプ取得（ログに使用）
        try:
            ts = utils_log.get_current_timestamp()
        except Exception:
            logging.exception("utils_log.get_current_timestamp() failed")
            ts = "UNKNOWN_TIME"

        # DB 更新: old_status を返す（存在しなければ None）
        try:
            old_status = db.update_status(person_id, status_int, ts)
        except Exception:
            logging.exception("db.update_status failed for id=%s", person_id)
            return 500, {"result": "error", "reason": "db_error", "detail": "update_status failed"}

        # 旧値が存在し、かつ異なる場合のみ状態変更ログを書く（設計通り）
        if old_status is not None and old_status != status_int:
            write_status_change_log(person_id, old_status, status_int, ts)

    # 3) 正常終了
    return 200, {"result": "ok"}
