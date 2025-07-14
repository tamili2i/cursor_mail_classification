# Production Dockerfile for User Service
FROM python:3.11-slim

WORKDIR /app

COPY services/user_service/ /app/
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 