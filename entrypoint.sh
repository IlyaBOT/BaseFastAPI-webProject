#!/usr/bin/bash
set -euo pipefail

HOST="${DB_HOST:-db}"
PORT="${DB_PORT:-3306}"
USER="${MYSQL_USER:-root}"
PASS="${MYSQL_PASSWORD:-}"
DBNAME="${MYSQL_DATABASE:-}"

echo "Waiting for MySQL at $HOST:$PORT..."

# пытаемся подключиться, пока не получится (таймаут 120s)
MAX_WAIT=120
WAITED=0
until mysqladmin ping -h"$HOST" -P"$PORT" --silent; do
  if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "MySQL did not become available after ${MAX_WAIT}s, exiting."
    exit 1
  fi
  echo "MySQL is not ready yet... (${WAITED}s)"
  sleep 1
  WAITED=$((WAITED+1))
done

echo "MySQL is up. Running migrations / table create..."
python - <<'PY'
from sqlmodel import SQLModel
from app.database import engine
from app.models import User
SQLModel.metadata.create_all(engine)
print("Tables created (if missing).")
PY

# Создаём админа, если надо (опционально)
python - <<'PY'
from app.crud import get_user_by_id, create_user_raw
admin = get_user_by_id(1)
if not admin:
    print("Creating admin user ID=1")
    create_user_raw(id=1, nickname='Admin', email='admin@example.com', password_plain='SuperAdmin2006')
else:
    print("Admin already exists.")
PY

echo "Starting uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
