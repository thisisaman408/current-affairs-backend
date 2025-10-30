#!/bin/bash
set -e

echo "🚀 Starting Current Affairs Backend..."

# Set default PORT if not set (for local development)
PORT=${PORT:-8000}

# Start Celery worker
echo "👷 Starting Celery worker (scheduled tasks)..."
celery -A workers.celery_tasks worker --loglevel=info &
CELERY_PID=$!
echo "✅ Celery worker started (PID: $CELERY_PID)"

# Start Celery Beat
echo "⏰ Starting Celery Beat (task scheduler)..."
celery -A workers.celery_tasks beat --loglevel=info &
BEAT_PID=$!
echo "✅ Celery Beat started (PID: $BEAT_PID)"

# Start PDF Processor
echo "📄 Starting PDF Processor worker..."
python workers/pdf_processor.py &
PDF_PID=$!
echo "✅ PDF Processor started (PID: $PDF_PID)"

# Start AI Generator
echo "🤖 Starting AI Generator worker..."
python workers/ai_generator.py &
AI_PID=$!
echo "✅ AI Generator started (PID: $AI_PID)"

# Wait for workers to initialize
echo "⏳ Waiting 5 seconds for workers to initialize..."
sleep 5

# Function to cleanup on exit
cleanup() {
    echo "⚠️ FastAPI stopped, shutting down workers..."
    kill $CELERY_PID $BEAT_PID $PDF_PID $AI_PID 2>/dev/null
    echo "🛑 All processes stopped"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Start FastAPI
echo "🌐 Starting FastAPI server..."
echo "📡 API will be available at: http://0.0.0.0:$PORT"
uvicorn src.main:app --host 0.0.0.0 --port $PORT

# Cleanup on normal exit
cleanup
