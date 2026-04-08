FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV API_BASE_URL=http://localhost:7860
ENV TASK_ID=easy

EXPOSE 7860

CMD ["uvicorn", "env.environment:app", "--host", "0.0.0.0", "--port", "7860"]
