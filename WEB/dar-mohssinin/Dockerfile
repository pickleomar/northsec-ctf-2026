FROM python:3.11-slim

# Node for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build && \
    mkdir -p /app/static && cp -r dist/* /app/static/

# App
COPY app.py bot.py ./

EXPOSE 5000
CMD ["python", "app.py"]
