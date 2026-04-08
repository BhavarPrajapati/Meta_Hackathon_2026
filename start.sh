#!/bin/bash
uvicorn env.environment:app --host 0.0.0.0 --port 7860 &
sleep 3
python inference.py
