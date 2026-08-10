FROM node:20-alpine AS web
WORKDIR /src/apps/web
COPY apps/web/package.json ./
RUN npm install
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY apps ./apps
COPY content ./content
COPY --from=web /src/apps/web/dist ./apps/web/dist
EXPOSE 8000
ENV LEARNING_DB_PATH=/data/learning-agent.db
CMD ["uvicorn","apps.api.app:app","--host","0.0.0.0","--port","8000"]
