FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements-prod.lock ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
RUN addgroup --system --gid 10001 appuser \
    && adduser --system --uid 10001 --ingroup appuser --no-create-home appuser \
    && mkdir -p /var/lib/opportunity-radar/archives \
    && chown -R appuser:appuser /app /var/lib/opportunity-radar
USER appuser
EXPOSE 8000 8080
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_WORKERS:-2}"]
