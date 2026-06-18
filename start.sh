#!/bin/bash
# Start script for OzLanka Outdoor Gear - runs all services without Docker
set -e

PROJECT_DIR="/projects/ozlanka-outdoor-gear"
VENV_DIR="/home/george/.venv-ozlanka"
LOG_DIR="/home/george/.local/log/ozlanka"
PID_DIR="/home/george/.local/run/ozlanka"

mkdir -p "$LOG_DIR" "$PID_DIR"

echo "=== OzLanka Outdoor Gear - Starting Services ==="

# Source .env
set -a
source "$PROJECT_DIR/.env"
set +a

# 1. Start Redis (if not running)
if ! pgrep -x redis-server > /dev/null 2>&1; then
    echo "Starting Redis..."
    /home/george/bin/redis-server --daemonize yes \
        --logfile "$LOG_DIR/redis.log" \
        --dir /tmp/redis-data \
        --save ""
    sleep 1
    echo "Redis started (PID: $(pgrep -x redis-server))"
else
    echo "Redis already running"
fi

# 2. Start PostgreSQL (if not running)
if ! "$PGHOME/bin/pg_isready" -q 2>/dev/null; then
    echo "Starting PostgreSQL..."
    export PGHOME="/home/george/pgsql"
    export PGDATA="$PGHOME/data"
    
    if [ ! -d "$PGDATA" ]; then
        echo "Initializing PostgreSQL data directory..."
        "$PGHOME/bin/initdb" -D "$PGDATA" --auth=trust --no-locale 2>&1
        # Allow local connections via trust and TCP via md5
        echo "host all all 127.0.0.1/32 trust" >> "$PGDATA/pg_hba.conf"
        echo "listen_addresses = '127.0.0.1'" >> "$PGDATA/postgresql.conf"
        echo "unix_socket_directories = '/tmp'" >> "$PGDATA/postgresql.conf"
        echo "port = 5432" >> "$PGDATA/postgresql.conf"
    fi
    
    "$PGHOME/bin/pg_ctl" -D "$PGDATA" -l "$LOG_DIR/postgres.log" -o "-k /tmp" start
    sleep 2
    
    # Create database and user
    "$PGHOME/bin/psql" -h /tmp -p 5432 -U george -d postgres -c "CREATE USER ozlanka WITH PASSWORD '$POSTGRES_PASSWORD';" 2>/dev/null || true
    "$PGHOME/bin/psql" -h /tmp -p 5432 -U george -d postgres -c "CREATE DATABASE ozlanka OWNER ozlanka;" 2>/dev/null || true
    "$PGHOME/bin/psql" -h /tmp -p 5432 -U george -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE ozlanka TO ozlanka;" 2>/dev/null || true
    
    echo "PostgreSQL started"
else
    echo "PostgreSQL already running"
fi

# 3. Start Backend (FastAPI)
echo "Starting Backend (FastAPI on port 8000)..."
cd "$PROJECT_DIR/backend"
"$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$PID_DIR/backend.pid"
sleep 2
echo "Backend started (PID: $(cat "$PID_DIR/backend.pid"))"

# 4. Start Celery Worker/Beat
echo "Starting Celery Worker..."
cd "$PROJECT_DIR/backend"
"$VENV_DIR/bin/celery" -A app.workers.celery_app.celery beat --loglevel=INFO > "$LOG_DIR/celery.log" 2>&1 &
echo $! > "$PID_DIR/celery.pid"
echo "Celery beat started (PID: $(cat "$PID_DIR/celery.pid"))"

# 5. Start Frontend (Next.js)
echo "Starting Frontend (Next.js on port 3002)..."
cd "$PROJECT_DIR/frontend"
BACKEND_INTERNAL_URL="http://127.0.0.1:8000" npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$PID_DIR/frontend.pid"
sleep 3
echo "Frontend started (PID: $(cat "$PID_DIR/frontend.pid"))"

echo ""
echo "=== All Services Started ==="
echo "Backend:   http://127.0.0.1:8000"
echo "Frontend:  http://127.0.0.1:3002"
echo "Redis:     redis://127.0.0.1:6379"
echo "PostgreSQL: postgresql://127.0.0.1:5432/ozlanka"
echo ""
echo "Logs: $LOG_DIR"
echo "Stop: bash $PROJECT_DIR/stop.sh"
