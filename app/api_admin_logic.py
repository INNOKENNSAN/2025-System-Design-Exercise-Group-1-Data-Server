"""
api_admin_logic.py

管理者用 API のビジネスロジックを集約するモジュール。

このファイルは Flask のルーティングから直接 DB を操作せず、
main.py から呼び出される形で以下の処理を担当する。

・人物一覧の取得
・人物の対応状況の更新

※ Web ルーティングは main.py 側の責務
"""

from typing import Dict, Any, List

import db
import logging


# ============================================================
# 管理者用：人物一覧取得
# ============================================================

def get_people_list() -> Dict[str, Any]:
    """
    管理画面用に、全人物の対応状況一覧を取得する。

    Returns
    -------
    dict
        {
            "result": "ok",
            "data": [
                {
                    "id":
                    "name": 
                    "department":
                    "grade":
                    "role":
                    "room":
                },
                ...
            ]
        }
        もしくは
        {
            "result": "error",
            "reason": str
        }
    """
    try:
        people = db.get_people_all()

        return {
            "result": "ok",
            "data": people
        }

    except Exception as e:
        logging.exception("人物一覧取得失敗")

        return {
            "result": "error",
            "reason": "failed_to_fetch_people"
        }
        
# ============================================================
# 管理者用：人物一括更新
# ============================================================

def apply_bulk_updates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    管理画面から送信された人物情報の一括更新を適用する。

    Parameters
    ----------
    records : List[dict]
        people テーブル1行分に相当する辞書の配列

    Returns
    -------
    dict
        db.apply_bulk_updates の戻り値をそのまま返す
    """
    try:
        result = db.apply_bulk_updates(records)

        return result

    except Exception as e:
        logging.exception("人物一括更新失敗")
        raise ApiError(
            message="failed to apply bulk updates",
            reason="bulk_update_failed",
            status_code=500
        )

# ============================================================
# 管理者用：人物追加
# ============================================================
def insert_person(default_data: Dict[str, Any]) -> int:
    """
    新規人物を people テーブルに追加する。
    """
    try:
        new_id = db.insert_person(default_data)

        return new_id

    except Exception:
        logging.exception("人物追加失敗")
        raise ApiError(
            message="failed to insert person",
            reason="insert_failed",
            status_code=500
        )

# ============================================================
# 管理者用：人物削除
# ============================================================
def delete_person(person_id: int) -> None:
    """
    指定された人物を削除する。
    """
    try:
        db.delete_person(person_id)

    except Exception:
        logging.exception("人物削除失敗")
        raise ApiError(
            message="failed to delete person",
            reason="delete_failed",
            status_code=500
        )



class ApiError(Exception):
    """
    管理 API 用の業務エラー例外
    """
    def __init__(self, message: str, reason: str = "api_error", status_code: int = 400):
        super().__init__(message)
        self.reason = reason
        self.status_code = status_code
