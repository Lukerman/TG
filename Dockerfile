# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash botuser && \
    chown -R botuser:botuser /app

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data && \
    chown -R botuser:botuser /app/data

# Switch to non-root user
USER botuser

# Create default environment file if it doesn't exist
RUN if [ ! -f .env ]; then \
    cp .env.example .env; \
    fi

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Check if required environment variables are set
required_vars = ['TELEGRAM_BOT_TOKEN', 'MONGO_CONNECTION_STRING']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'Missing required environment variables: {missing}')
    sys.exit(1)

# Test basic imports
try:
    from telegram import Update
    from motor.motor_asyncio import AsyncIOMotorClient
    print('Health check passed')
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
"

# Expose port (if bot needs to expose web interface)
EXPOSE 8080

# Volume for persistent data
VOLUME ["/app/data"]

# Set the entrypoint
ENTRYPOINT ["python", "bot.py"]

# Default command
CMD [""]