#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
python - <<'EOF'
import time, os, psycopg2

url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/cv_maker_db")
while True:
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print("PostgreSQL is ready.")
        break
    except psycopg2.OperationalError:
        print("  not ready yet, retrying in 2s...")
        time.sleep(2)
EOF

exec uvicorn main:app --host 0.0.0.0 --port 8192
