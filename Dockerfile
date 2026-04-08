FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

ENV PYTHONPATH=/app
ENV API_BASE_URL=http://localhost:7860
ENV TASK_ID=all

EXPOSE 7860

CMD ["./start.sh"]
