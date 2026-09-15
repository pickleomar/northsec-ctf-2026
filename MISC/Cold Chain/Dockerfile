FROM python:3.12-slim

WORKDIR /app
COPY server /app/server

ENV PYTHONUNBUFFERED=1
EXPOSE 31337

CMD ["python", "-m", "server.server"]

