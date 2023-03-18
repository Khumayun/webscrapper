FROM python:3.10-slim

ENV PYTHONUNBUFFERED True

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y chromium

ENTRYPOINT gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
