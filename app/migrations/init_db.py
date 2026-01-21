# migrations/init_db.py
# データベース初期化および初期データ投入用スクリプト
#
# 本スクリプトは Flask アプリからは直接呼び出されず、
# 開発時・初期セットアップ時に手動実行することを想定している。
#
# 実行例:
#   python migrations/init_db.py
#
# 注意:
# - DB 操作はすべて db.py に委譲し、SQL を直接書かない
# - 既存データがある場合は多重投入を防ぐ

import sys
from typing import List, Dict

# app ディレクトリを import パスに追加（直接実行対策）
sys.path.append("..")

from app import db
from app import utils_log


def _initial_people_data() -> List[Dict[str, str]]:
    """
    初期投入する人物データを返す。
    設計仕様に基づき、最小限の項目のみ設定する。
    """
    return [
        {
            "name": "山田 太郎",
            "department": "情報工学科",
            "grade": "3年",
            "role": "学生",
            "room": "A101",
        },
        {
            "name": "佐藤 花子",
            "department": "情報工学科",
            "grade": "4年",
            "role": "学生",
            "room": "A102",
        },
        {
            "name": "鈴木 一郎",
            "department": "情報工学科",
            "grade": "",
            "role": "教員",
            "room": "教員室",
        },
    ]


def main() -> None:
    """
    初期化処理のメイン関数。
    """
    print("=== Sensei Switch DB 初期化開始 ===")

    # ログディレクトリ準備（本体と同一仕様）
    try:
        utils_log.ensure_log_dir_exists()
    except Exception as e:
        print(f"[WARN] ログディレクトリ初期化に失敗しました: {e}")

    # DB 初期化（テーブル作成）
    print("DB スキーマを初期化しています...")
    db.init_db()
    print("DB 初期化完了")

    # 初期人物データ投入
    people = _initial_people_data()
    inserted_ids = []

    print("初期人物データを投入します...")
    for person in people:
        try:
            person_id = db.insert_person(person)
            inserted_ids.append(person_id)
            print(f"  追加: id={person_id}, name={person.get('name')}")
        except Exception as e:
            print(f"[ERROR] 人物データ投入失敗: {person} ({e})")

    # 初期ステータス（全員 0 = 不在 とする）
    print("初期ステータスを設定します...")
    for pid in inserted_ids:
        try:
            # timestamp は utils_log を使用
            ts = utils_log.get_current_timestamp()
            db.update_status(pid, 0, ts)
        except Exception as e:
            print(f"[WARN] ステータス初期化失敗: id={pid} ({e})")

    print("=== DB 初期化処理 完了 ===")


if __name__ == "__main__":
    main()
