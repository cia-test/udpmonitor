FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY scripts/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY src/ /app/src/
COPY main.py /app/

# Create directory for database
RUN mkdir -p /app/data

# Expose ports
EXPOSE 5000 8888/udp

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_PATH=/app/data/udpmonitor.db

# Run the application
CMD ["python", "main.py", "--db-path", "/app/data/udpmonitor.db"]

