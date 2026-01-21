# utils_log.py
# ログ関連の共通ユーティリティ
#
# 設計仕様書 4.5 節に基づき、以下の機能のみを提供する：
#  - ログ保存ディレクトリの初期化
#  - ログ用タイムスタンプ生成
#  - ログファイルへの1行追記
#
# 本モジュールは「最低限の責務」に留め、
# ログ内容の生成やエラー制御は呼び出し側に委ねる。

import os
import logging
from datetime import datetime
from typing import Optional


# デフォルトのログディレクトリ
DEFAULT_LOG_DIR = "/var/log/sensei_switch"

# 環境変数名
ENV_LOG_DIR = "SENSEI_LOG_DIR"


def _get_log_dir() -> str:
    """
    使用するログディレクトリを返す。
    環境変数があればそれを優先する。
    """
    return os.environ.get(ENV_LOG_DIR, DEFAULT_LOG_DIR)


def ensure_log_dir_exists() -> None:
    """
    ログ保存用ディレクトリを作成・確認する。
    - 既に存在する場合は何もしない
    - 作成できない、または書き込み不可の場合は例外を送出する
    """
    log_dir = _get_log_dir()

    # ディレクトリ作成（存在していてもエラーにしない）
    os.makedirs(log_dir, exist_ok=True)

    # 書き込み可能かを簡易チェック
    test_path = os.path.join(log_dir, ".write_test")
    try:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_path)
    except Exception as e:
        raise PermissionError(f"ログディレクトリに書き込めません: {log_dir}") from e


def get_current_timestamp() -> str:
    """
    現在時刻をログ用の文字列として返す。
    フォーマット: YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log_line(filename: str, line: str) -> None:
    """
    指定されたログファイルに1行追記する。

    引数:
      - filename: ログファイル名（例: "status_change.log"）
      - line: 追記する1行（改行は自動付与）

    注意:
      - 書き込み失敗時は例外を送出する
      - 呼び出し側で try/except することを前提とする
    """
    if "/" in filename or "\\" in filename:
        raise ValueError("filename にパス区切り文字を含めることはできません")

    log_dir = _get_log_dir()
    log_path = os.path.join(log_dir, filename)

    # 追記モードで書き込み
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

# -------------------------------------------------------------
# 管理系ログ出力（設計 4.6 節）
# -------------------------------------------------------------
def log_info(message: str) -> None:
    """
    管理系 INFO ログを出力する。
    """
    try:
        ts = get_current_timestamp()
        line = f"{ts} INFO {message}"
        write_log_line("admin.log", line)
    except Exception:
        logging.exception("log_info failed")


def log_error(message: str) -> None:
    """
    管理系 ERROR ログを出力する。
    """
    try:
        ts = get_current_timestamp()
        line = f"{ts} ERROR {message}"
        write_log_line("admin.log", line)
    except Exception:
        logging.exception("log_error failed")
