# db.py
# SQLite を用いた DB 層。設計仕様書（4.5節）に準拠して
# people / status テーブルの CRUD とユーティリティを提供する。
#
# 提供関数（主要）:
# - init_db() -> None
# - person_exists(person_id: int) -> bool
# - update_status(person_id: int, status: int, timestamp: str) -> Optional[int]
# - get_status_table() -> List[dict]
# - get_people_all() -> List[dict]
# - insert_person(default_data: dict) -> int
# - delete_person(person_id: int) -> None
# - apply_bulk_updates(records: List[dict]) -> dict
#
# 設計考慮:
# - status テーブルは person_id を PRIMARY KEY として「最新状態のみ」を保持する方式
# - SQL は必ずパラメタ化して実行（SQLインジェクション対策）
# - トランザクション（BEGIN/COMMIT/ROLLBACK）を用いて一括更新の一貫性を確保
# - 外部キーを有効化（必要に応じて）して整合性を保つ
# - DB ファイルはデフォルトで /app/database.db（Docker の WORKDIR /app を想定）
#
# 注意:
# - 実運用で大量の同時書き込みがある場合、SQLite から PostgreSQL 等に移行を検討してください。

import sqlite3
from typing import List, Dict, Optional, Any
import os
import logging

# DB ファイルのパス（コンテナ内の /app を想定）
DB_PATH = os.environ.get("SENSEI_DB_PATH", "database.db")


def _get_conn() -> sqlite3.Connection:
    """
    SQLite 接続を返す。外部キー制約を有効化して返す。
    detect_types はデフォルトでそのまま。
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    # 外部キー制約を有効にする（SQLite のデフォルトは無効）
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """
    DB ファイルとテーブルを作成する（存在しない場合）。
    - people テーブル
    - status テーブル（person_id を PRIMARY KEY として最新状態のみを保持）
    """
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department TEXT,
                grade TEXT,
                role TEXT,
                room TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS status (
                person_id INTEGER PRIMARY KEY,
                status INTEGER,
                timestamp TEXT,
                FOREIGN KEY(person_id) REFERENCES people(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def person_exists(person_id: int) -> bool:
    """
    指定した person_id が people テーブルに存在するかを返す。
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM people WHERE id = ? LIMIT 1", (person_id,))
        row = cur.fetchone()
        return row is not None
    finally:
        conn.close()


def update_status(person_id: int, status: int, timestamp: str) -> Optional[int]:
    """
    person_id に対するステータスを更新する。
    - 旧値が存在しなければ INSERT して None を返す（初回登録）。
    - 旧値が存在すれば old_status を返す。旧値と異なる場合のみ DB を更新する（設計準拠）。
    引数:
      - person_id: int
      - status: int (0 or 1)
      - timestamp: str (YYYY-MM-DD HH:MM:SS)
    戻り値:
      - old_status: int  -> 既存レコードの status（存在した場合）
      - None: -> 旧値が存在しない（初回挿入）
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT status FROM status WHERE person_id = ?", (person_id,))
        row = cur.fetchone()
        if row is None:
            # 初回挿入
            cur.execute(
                "INSERT INTO status (person_id, status, timestamp) VALUES (?, ?, ?)",
                (person_id, status, timestamp),
            )
            conn.commit()
            return None
        else:
            old_status = int(row["status"])
            # 旧値と異なるときのみ更新（仕様通り）
            if old_status != status:
                cur.execute(
                    "UPDATE status SET status = ?, timestamp = ? WHERE person_id = ?",
                    (status, timestamp, person_id),
                )
                conn.commit()
            # 旧値（更新の有無にかかわらず返す）
            return old_status
    finally:
        conn.close()


def get_status_table() -> List[Dict[str, Any]]:
    """
    閲覧用の一覧データを返す。
    各レコードは以下のキーを持つ:
      - id, name, department, grade, role, room, status, timestamp
    並び順: department ASC, room ASC, name ASC
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id as id, p.name as name, p.department as department, p.grade as grade,
                   p.role as role, p.room as room,
                   s.status as status, s.timestamp as timestamp
            FROM people p
            LEFT JOIN status s ON p.id = s.person_id
            ORDER BY COALESCE(p.department, ''), COALESCE(p.room, ''), COALESCE(p.name, '')
            """
        )
        rows = cur.fetchall()
        result: List[Dict[str, Any]] = []
        for r in rows:
            result.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "department": r["department"],
                    "grade": r["grade"],
                    "role": r["role"],
                    "room": r["room"],
                    "status": (None if r["status"] is None else int(r["status"])),
                    "timestamp": r["timestamp"],
                }
            )
        return result
    finally:
        conn.close()


def get_people_all() -> List[Dict[str, Any]]:
    """
    管理画面用の people 一覧を返す。
    並び順: department ASC、room ASC、name ASC
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, department, grade, role, room
            FROM people
            ORDER BY COALESCE(department, ''), COALESCE(room, ''), COALESCE(name, '')
            """
        )
        rows = cur.fetchall()
        result: List[Dict[str, Any]] = []
        for r in rows:
            result.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "department": r["department"],
                    "grade": r["grade"],
                    "role": r["role"],
                    "room": r["room"],
                }
            )
        return result
    finally:
        conn.close()


def insert_person(default_data: Dict[str, Any]) -> int:
    """
    people テーブルに新規人物を挿入する。
    - default_data は name, department, grade, role, room の任意フィールドを含む辞書。
    - 戻り値は新規に採番された person_id (int)。
    """
    name = default_data.get("name")
    department = default_data.get("department")
    grade = default_data.get("grade")
    role = default_data.get("role")
    room = default_data.get("room")

    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO people (name, department, grade, role, room) VALUES (?, ?, ?, ?, ?)",
            (name, department, grade, role, room),
        )
        new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def delete_person(person_id: int) -> None:
    """
    people および関連する status を物理削除する。
    トランザクションで一括削除して rollback に対応。
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("DELETE FROM status WHERE person_id = ?", (person_id,))
        cur.execute("DELETE FROM people WHERE id = ?", (person_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        logging.exception("delete_person rollback due to exception for id=%s", person_id)
        raise
    finally:
        conn.close()


def apply_bulk_updates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    管理画面からの一括更新をトランザクションで適用する。
    records は辞書のリストで、各辞書は次のような構造を想定:
      - id: (既存行の id, 新規の場合は None または absent)
      - name, department, grade, role, room: 各フィールド（編集後の値）
    動作:
      - id がある場合は UPDATE を行う
      - id が無い場合は INSERT を行う
    戻り値:
      - summary: {'updated': n, 'inserted': m, 'errors': [ ... ] }
    """
    inserted = 0
    updated = 0
    errors: List[str] = []

    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN")
        for rec in records:
            try:
                pid = rec.get("id")
                name = rec.get("name")
                department = rec.get("department")
                grade = rec.get("grade")
                role = rec.get("role")
                room = rec.get("room")

                if pid is None or pid == "" or (isinstance(pid, str) and pid.lower() == "null"):
                    # 新規挿入
                    cur.execute(
                        "INSERT INTO people (name, department, grade, role, room) VALUES (?, ?, ?, ?, ?)",
                        (name, department, grade, role, room),
                    )
                    inserted += 1
                else:
                    # 既存更新
                    try:
                        pid_int = int(pid)
                    except Exception:
                        raise ValueError(f"invalid id value: {pid}")

                    cur.execute(
                        """
                        UPDATE people
                        SET name = ?, department = ?, grade = ?, role = ?, room = ?
                        WHERE id = ?
                        """,
                        (name, department, grade, role, room, pid_int),
                    )
                    if cur.rowcount > 0:
                        updated += 1
                    else:
                        # 対象行が無かった（ID 不正等）
                        errors.append(f"no_target_for_update id={pid_int}")
            except Exception as e_inner:
                # レコード単位のエラーを収集して続行
                logging.exception("apply_bulk_updates record error: %s", e_inner)
                errors.append(f"record_error: {str(e_inner)}")
        conn.commit()
    except Exception:
        conn.rollback()
        logging.exception("apply_bulk_updates rolled back due to exception")
        raise
    finally:
        conn.close()

    return {"updated": updated, "inserted": inserted, "errors": errors}
