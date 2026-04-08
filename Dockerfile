FROM python:3.10-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV API_BASE_URL=http://localhost:7860
ENV ENV_BASE_URL=http://localhost:7860
ENV TASK_ID=all

EXPOSE 7860

RUN chmod +x start.sh

CMD ["bash", "start.sh"]
