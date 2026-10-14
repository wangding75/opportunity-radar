FROM node:22-alpine AS react-build
WORKDIR /ui
ARG VITE_ENABLE_API=true
ENV VITE_ENABLE_API=$VITE_ENABLE_API
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements-prod.lock ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=react-build /ui/dist ./react-static
RUN addgroup --system --gid 10001 appuser \
    && adduser --system --uid 10001 --ingroup appuser --no-create-home appuser \
    && mkdir -p /var/lib/opportunity-radar/archives \
    && chown -R appuser:appuser /app /var/lib/opportunity-radar
USER appuser
EXPOSE 8000 8080
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_WORKERS:-2}"]
