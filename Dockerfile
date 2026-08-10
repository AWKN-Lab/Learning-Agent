FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY apps ./apps
COPY content ./content
EXPOSE 8000
ENV LEARNING_DB_PATH=/data/learning-agent.db
CMD ["uvicorn","apps.api.app:app","--host","0.0.0.0","--port","8000"]
