#!/bin/sh
set -e

DB_FILE="/app/database.db"

echo "[entrypoint] checking database..."

# DB が存在しない or 0 byte の場合のみ初期化
if [ ! -s "$DB_FILE" ]; then
  echo "[entrypoint] initializing database..."
  python migrations/init_db.py
else
  echo "[entrypoint] database already exists"
fi

exec "$@"
