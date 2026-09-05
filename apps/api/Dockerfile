FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api ./

RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=3000
EXPOSE 3000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 3000"]
