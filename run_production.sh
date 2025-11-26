#!/bin/bash
# Production startup script for udpmonitor
# This script runs uvicorn with multiple workers for production use

set -e

# Default values
UDP_HOST=${UDP_HOST:-0.0.0.0}
UDP_PORT=${UDP_PORT:-8888}
API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-5000}
DB_PATH=${DB_PATH:-udpmonitor.db}
RETENTION_DAYS=${RETENTION_DAYS:-1.0}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Start the UDP listener in background
python3 -c "
import sys
sys.path.insert(0, '.')
from storage import MessageStorage
from udp_listener import UDPListener
import threading
import time
import signal

storage = MessageStorage(db_path='$DB_PATH')
listener = UDPListener(host='$UDP_HOST', port=$UDP_PORT, storage=storage)
listener.start()

# Keep running
def signal_handler(sig, frame):
    listener.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

while True:
    time.sleep(1)
" &
UDP_PID=$!

# Start cleanup worker in background
python3 -c "
import sys
sys.path.insert(0, '.')
from storage import MessageStorage
import threading
import time
import signal
from datetime import datetime, timedelta

storage = MessageStorage(db_path='$DB_PATH')
retention_days = $RETENTION_DAYS
running = True

def cleanup_worker():
    while running:
        try:
            now = datetime.now()
            today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if today_midnight <= now:
                next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                next_midnight = today_midnight
            sleep_seconds = (next_midnight - now).total_seconds()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            if not running:
                break
            deleted_count = storage.delete_old_messages(days=retention_days)
            if deleted_count > 0:
                print(f'[Cleanup] Deleted {deleted_count} messages older than {retention_days} day(s)')
        except Exception as e:
            print(f'[Cleanup] Error: {e}')
            time.sleep(3600)

def signal_handler(sig, frame):
    global running
    running = False
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

thread = threading.Thread(target=cleanup_worker, daemon=True)
thread.start()

while True:
    time.sleep(1)
" &
CLEANUP_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $UDP_PID 2>/dev/null || true
    kill $CLEANUP_PID 2>/dev/null || true
    wait
}

trap cleanup EXIT INT TERM

# Start uvicorn with multiple workers
echo "Starting UDP Monitor in production mode..."
echo "UDP Listener: $UDP_HOST:$UDP_PORT (PID: $UDP_PID)"
echo "REST API: http://$API_HOST:$API_PORT"
echo "Workers: $WORKERS"
echo "Log Level: $LOG_LEVEL"

uvicorn rest_api:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --access-log \
    --no-use-colors

