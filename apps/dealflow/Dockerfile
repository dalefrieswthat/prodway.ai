FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY apps/dealflow/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared packages
COPY packages ./packages

# Copy app
COPY apps/dealflow ./

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

CMD ["python", "main.py"]
