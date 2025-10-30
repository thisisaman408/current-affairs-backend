#!/bin/bash
set -e

echo "🚀 Starting Current Affairs Backend..."

# Set default PORT
PORT=${PORT:-8000}

# Start Celery worker WITH embedded beat (single process!)
echo "👷 Starting Celery worker with Beat scheduler..."
celery -A workers.celery_tasks worker --beat --loglevel=info &
CELERY_PID=$!
echo "✅ Celery worker + beat started (PID: $CELERY_PID)"

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

# Wait for workers
echo "⏳ Waiting 5 seconds for workers to initialize..."
sleep 5

# Cleanup function
cleanup() {
    echo "⚠️ FastAPI stopped, shutting down workers..."
    kill $CELERY_PID $PDF_PID $AI_PID 2>/dev/null
    echo "🛑 All processes stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI
echo "🌐 Starting FastAPI server..."
echo "📡 API will be available at: http://0.0.0.0:$PORT"
uvicorn src.main:app --host 0.0.0.0 --port $PORT

cleanup
