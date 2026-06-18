#!/bin/bash
# Stop script for OzLanka Outdoor Gear

PROJECT_DIR="/projects/ozlanka-outdoor-gear"
PID_DIR="/home/george/.local/run/ozlanka"

echo "=== OzLanka Outdoor Gear - Stopping Services ==="

stop_pid() {
    local name="$1"
    local pid_file="$PID_DIR/$name.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -9 "$pid" 2>/dev/null || true
        else
            echo "$name not running (stale PID file)"
        fi
        rm -f "$pid_file"
    else
        echo "$name PID file not found"
    fi
}

stop_pid "frontend"
stop_pid "celery"
stop_pid "backend"

# Stop Redis
if pgrep -x redis-server > /dev/null 2>&1; then
    echo "Stopping Redis..."
    /home/george/bin/redis-cli shutdown nosave 2>/dev/null || true
    sleep 1
fi

# Stop PostgreSQL
PGHOME="/home/george/pgsql"
PGDATA="$PGHOME/data"
if [ -d "$PGDATA" ]; then
    echo "Stopping PostgreSQL..."
    "$PGHOME/bin/pg_ctl" -D "$PGDATA" stop 2>/dev/null || true
fi

echo "=== All Services Stopped ==="
