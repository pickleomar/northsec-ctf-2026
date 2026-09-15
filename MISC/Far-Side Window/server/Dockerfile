FROM python:3.12-slim

WORKDIR /app

COPY common.py .
COPY server.py .
COPY relay_downlink.bin .

EXPOSE 31337

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1', int(os.getenv('PORT','31337'))), 2); s.close()"

CMD ["python", "server.py"]
