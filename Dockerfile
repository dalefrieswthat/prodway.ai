FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY apps/sowflow/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared packages (for future use)
COPY packages ./packages

# Copy app
COPY apps/sowflow ./

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app

# Create data directory for file-based storage
RUN mkdir -p /app/data && chown -R app:app /app/data

USER app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["python", "main.py"]
