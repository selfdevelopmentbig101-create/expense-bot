FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

# Run as a normal user, never as root. The data folder is the only writable place.
RUN useradd --create-home --uid 1000 bot \
    && mkdir -p /app/data \
    && chown -R bot:bot /app/data
USER bot
VOLUME ["/app/data"]

# The bot touches a file every 30 seconds; no heartbeat for 2 minutes = unhealthy.
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-m", "app.healthcheck"]

# Update the database structure, then start the bot (exec: Ctrl+C / docker stop reach the bot).
CMD ["sh", "-c", "alembic upgrade head && exec python -m app"]
