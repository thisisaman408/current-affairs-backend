#!/bin/bash
set -e

echo "🚀 Starting Current Affairs Backend..."

# Set default PORT
PORT=${PORT:-10000}

# Start Celery worker WITH embedded beat (single process!)
echo "👷 Starting Celery worker with Beat scheduler..."
celery -A workers.celery_tasks worker --beat --loglevel=info &
CELERY_PID=$!
echo "✅ Celery worker + beat started (PID: $CELERY_PID)"

# Wait for Celery to initialize
echo "⏳ Waiting 3 seconds for Celery to initialize..."
sleep 3

# Cleanup function
cleanup() {
    echo "⚠️ FastAPI stopped, shutting down Celery..."
    kill $CELERY_PID 2>/dev/null || true
    echo "🛑 All processes stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI (main process - keeps script alive)
echo "🌐 Starting FastAPI server..."
echo "📡 API will be available at: http://0.0.0.0:$PORT"
uvicorn src.main:app --host 0.0.0.0 --port $PORT

cleanup
