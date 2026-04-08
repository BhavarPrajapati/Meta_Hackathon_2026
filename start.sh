#!/bin/bash
set -e

echo "[START] Starting AI CEO Simulator environment server..."

# Start the FastAPI server in the background
uvicorn env.environment:app --host 0.0.0.0 --port 7860 --workers 1 &
SERVER_PID=$!

# Wait for server to be ready
echo "[INFO] Waiting for server to start..."
for i in $(seq 1 30); do
    if curl -s http://localhost:7860/info > /dev/null 2>&1; then
        echo "[INFO] Server is ready!"
        break
    fi
    sleep 2
done

# Run inference on all tasks
echo "[INFO] Running inference on all tasks..."
TASK_ID=all ENV_BASE_URL=http://localhost:7860 python inference.py

echo "[INFO] Inference complete."

# Keep server running after inference
wait $SERVER_PID
