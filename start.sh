#!/bin/bash
set -e

uvicorn env.environment:app --host 0.0.0.0 --port 7860 --workers 1 &
SERVER_PID=$!

sleep 5

python inference.py

wait $SERVER_PID
