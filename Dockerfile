FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=demo \
    LEARNING_DB_PATH=/data/learning-agent.db

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /data /app/scripts \
    && chown -R app:app /data /app

COPY --chown=app:app apps ./apps
COPY --chown=app:app content ./content
COPY --chown=app:app scripts/cleanup_sessions.py ./scripts/cleanup_sessions.py

VOLUME ["/data"]
USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/live', timeout=2).read()" || exit 1

CMD ["uvicorn","apps.api.app:app","--host","0.0.0.0","--port","8000"]
