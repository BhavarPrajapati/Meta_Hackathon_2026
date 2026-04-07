FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face default port
EXPOSE 7860

# Point PYTHONPATH to /app so we can import 'env' and 'agent'
ENV PYTHONPATH=/app

CMD ["uvicorn", "env.environment:app", "--host", "0.0.0.0", "--port", "7860"]
