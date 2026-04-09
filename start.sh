#!/bin/bash
set -e

# Start the FastAPI server in the background
uvicorn env.environment:app --host 0.0.0.0 --port 7860 --workers 1 &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 30); do
    if curl -s http://localhost:7860/info > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Run inference on all tasks
TASK_ID=all ENV_BASE_URL=http://localhost:7860 PYTHONUNBUFFERED=1 python inference.py

# Keep server running after inference
wait $SERVER_PID
