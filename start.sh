#!/bin/bash
# Master startup script - runs ALL workers + FastAPI in one container

echo "🚀 Starting Current Affairs Backend..."

# ===== 1. START CELERY WORKER (Scheduled Tasks) =====
echo "👷 Starting Celery worker (scheduled tasks)..."
celery -A workers.celery_tasks worker --loglevel=info --concurrency=1 &
CELERY_PID=$!
echo "✅ Celery worker started (PID: $CELERY_PID)"

# ===== 2. START CELERY BEAT (Cron Scheduler) =====
echo "⏰ Starting Celery Beat (task scheduler)..."
celery -A workers.celery_tasks beat --loglevel=info &
BEAT_PID=$!
echo "✅ Celery Beat started (PID: $BEAT_PID)"

# ===== 3. START PDF PROCESSOR WORKER =====
echo "📄 Starting PDF Processor worker..."
python workers/pdf_processor.py &
PDF_PID=$!
echo "✅ PDF Processor started (PID: $PDF_PID)"

# ===== 4. START AI GENERATOR WORKER =====
echo "🤖 Starting AI Generator worker..."
python workers/ai_generator.py &
AI_PID=$!
echo "✅ AI Generator started (PID: $AI_PID)"

# Give all workers time to initialize
echo "⏳ Waiting 5 seconds for workers to initialize..."
sleep 5

# ===== 5. START FASTAPI SERVER (Foreground) =====
echo "🌐 Starting FastAPI server..."
echo "📡 API will be available at: http://0.0.0.0:$PORT"
uvicorn src.main:app --host 0.0.0.0 --port $PORT

# If FastAPI crashes, kill all workers
echo "⚠️ FastAPI stopped, shutting down workers..."
kill $CELERY_PID $BEAT_PID $PDF_PID $AI_PID 2>/dev/null
echo "🛑 All processes stopped"
