# UDP Monitor

A production-ready system that listens for UDP datagrams, echoes them back with an "ECHO:" prefix, stores them in a database, and provides a REST API to query the stored messages.

## Features

- **UDP Listener**: Listens on a configurable port for UDP datagrams
- **Echo Response**: Echoes back received messages prefixed with "ECHO:"
- **Message Storage**: Stores all received datagrams in SQLite database with connection metadata (IP, port, timestamp, data)
- **REST API**: FastAPI-based REST endpoint to query stored messages
- **Automatic Cleanup**: Nightly deletion of messages older than the retention period (default: 1 day)
- **Docker Support**: Fully dockerized with Docker Compose

## Quick Start with Docker

The easiest way to run UDP Monitor is with Docker Compose:

```bash
docker-compose up -d
```

This will:
- Start UDP listener on `0.0.0.0:8888`
- Start REST API on `0.0.0.0:5000`
- Create/use SQLite database in `./data/udpmonitor.db`
- Automatically delete messages older than 1 day every night at midnight

Access the API:
- REST API: http://localhost:5000
- API Documentation: http://localhost:5000/docs
- Health Check: http://localhost:5000/health

## Installation (Local Development)

### Option 1: Install as editable package (Recommended)

```bash
# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the application
python main.py
```

### Option 2: Manual setup

1. Install dependencies:
```bash
pip install -r scripts/requirements.txt
```

2. Set PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

3. Run the application:
```bash
python main.py
```

## Project Structure

```
udpmonitor/
├── src/
│   └── udpmonitor/          # Source package
│       ├── __init__.py
│       ├── storage.py       # Database storage
│       ├── udp_listener.py  # UDP listener
│       ├── rest_api.py       # FastAPI REST API
│       └── udpfetch.py       # Python module for fetching messages
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_storage.py      # Storage tests
│   ├── test_udpfetch.py     # UDP fetch tests
│   └── test_udp_client.py   # UDP client tests
├── scripts/
│   └── requirements.txt     # Python dependencies
├── data/                     # Database storage (created at runtime)
├── main.py                   # Application entry point
├── Dockerfile                # Docker image definition
├── compose.yaml              # Docker Compose configuration
├── pytest.ini                # Pytest configuration
└── README.md
```

## Usage

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Local Development

```bash
# Basic usage
python main.py

# Custom configuration
python main.py --udp-host 0.0.0.0 --udp-port 8888 --api-host 127.0.0.1 --api-port 5000 --db-path mydb.db --retention-days 7
```

### Command Line Options

- `--udp-host`: Host for UDP listener (default: 0.0.0.0)
- `--udp-port`: Port for UDP listener (default: 8888)
- `--api-host`: Host for REST API (default: 0.0.0.0)
- `--api-port`: Port for REST API (default: 5000)
- `--db-path`: Path to SQLite database file (default: udpmonitor.db)
- `--retention-days`: Number of days to retain messages before automatic deletion (default: 1.0)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--workers`: Number of uvicorn workers (default: 1, use 4+ for production)

## REST API Endpoints

The API is built with FastAPI and provides automatic OpenAPI documentation at `/docs` and `/redoc`.

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

### GET /messages

Retrieve stored messages with optional filtering and pagination.

**Query Parameters:**
- `limit`: Maximum number of messages to return (default: 100)
- `offset`: Number of messages to skip (default: 0)
- `client_ip`: Filter by client IP address (optional)
- `client_port`: Filter by client port (optional)

**Example:**
```bash
curl http://localhost:5000/messages?limit=10&offset=0
curl http://localhost:5000/messages?client_ip=192.168.1.100
curl http://localhost:5000/messages?client_ip=192.168.1.100&client_port=54321
```

### GET /messages/count

Get the total count of stored messages.

**Example:**
```bash
curl http://localhost:5000/messages/count
```

### GET /messages/{id}

Get a specific message by ID.

**Example:**
```bash
curl http://localhost:5000/messages/1
```

### GET /health

Health check endpoint.

**Example:**
```bash
curl http://localhost:5000/health
```

### POST /cleanup

Manually trigger cleanup of old messages.

**Query Parameters:**
- `days`: Number of days to retain (optional, defaults to 1.0 if not specified)

**Example:**
```bash
curl -X POST http://localhost:5000/cleanup
curl -X POST http://localhost:5000/cleanup?days=7
```

## Python Module: udpfetch

A simple Python module for retrieving messages from the database.

### Basic Usage

```python
from udpmonitor import udpfetch

# Get all messages (or last N messages)
messages = udpfetch.get_messages(limit=10)

# Access message properties
for msg in messages:
    print(f"ID: {msg.id}")
    print(f"IP: {msg.ip}")
    print(f"Port: {msg.port}")
    print(f"Message: {msg.message}")
    print(f"Timestamp: {msg.timestamp}")
    print(f"Data size: {msg.data_size} bytes")
    print(f"Raw data: {msg.data}")
    print("-" * 40)

# Get latest message
latest = udpfetch.get_latest_message()
if latest:
    print(f"Latest: {latest.ip}:{latest.port} - {latest.message}")

# Filter by IP or port
messages_from_ip = udpfetch.get_messages(client_ip="192.168.1.100")
messages_from_port = udpfetch.get_messages(client_port=54321)

# Get message count
count = udpfetch.get_message_count()
print(f"Total messages: {count}")
```

## Testing

### Running Tests

The project includes comprehensive pytest tests:

```bash
# Install package with dev dependencies (includes pytest)
pip install -e ".[dev]"

# Or install test dependencies manually
pip install -r scripts/requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_udpfetch.py

# Run with coverage (requires pytest-cov)
pytest --cov=src/udpmonitor --cov-report=html
```

### Test Structure

- `tests/test_storage.py` - Tests for database storage functionality
- `tests/test_udpfetch.py` - Tests for the udpfetch module
- `tests/test_udp_client.py` - Tests for UDP client functionality

### Manual Testing

**Send UDP Message using netcat:**
```bash
echo "Hello, World!" | nc -u localhost 8888
```

**Send UDP Message using Python:**
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(b"Hello, World!", ("localhost", 8888))
data, addr = sock.recvfrom(1024)
print(f"Received: {data}")
sock.close()
```

**Query Messages via REST API:**
```bash
# Get all messages
curl http://localhost:5000/messages

# Get last 10 messages
curl http://localhost:5000/messages?limit=10

# Filter by IP
curl http://localhost:5000/messages?client_ip=127.0.0.1
```

## Automatic Cleanup

The system automatically deletes messages older than the retention period every night at midnight. This helps limit database size and prevents unbounded growth.

### How It Works

- A background thread runs continuously
- Every night at midnight (00:00:00), it deletes all messages older than the retention period
- The retention period is configurable via `--retention-days` (default: 1.0 days)
- You can also manually trigger cleanup using the `POST /cleanup` endpoint

### Examples

**Keep messages for 7 days:**
```bash
python main.py --retention-days 7
```

**Keep messages for 12 hours:**
```bash
python main.py --retention-days 0.5
```

**Manually trigger cleanup:**
```bash
curl -X POST http://localhost:5000/cleanup?days=1
```

## Production Deployment

### Docker

For production with Docker Compose, you can customize the configuration in `compose.yaml`:

```yaml
environment:
  - RETENTION_DAYS=7.0
  - LOG_LEVEL=INFO
```

### Environment Variables

- `UDP_HOST`: Host for UDP listener (default: 0.0.0.0)
- `UDP_PORT`: Port for UDP listener (default: 8888)
- `API_HOST`: Host for REST API (default: 0.0.0.0)
- `API_PORT`: Port for REST API (default: 5000)
- `DB_PATH`: Path to SQLite database file (default: /app/data/udpmonitor.db)
- `RETENTION_DAYS`: Number of days to retain messages (default: 1.0)
- `LOG_LEVEL`: Logging level (default: INFO)

## Database Schema

The SQLite database stores messages with the following schema:

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    client_ip TEXT NOT NULL,
    client_port INTEGER NOT NULL,
    data BLOB NOT NULL,
    data_text TEXT,
    data_size INTEGER NOT NULL
);
```

## Architecture

- **src/udpmonitor/storage.py**: SQLite-based storage module with thread-safe operations and cleanup functionality
- **src/udpmonitor/udp_listener.py**: UDP listener that receives datagrams, echoes them, and stores them
- **src/udpmonitor/rest_api.py**: FastAPI-based REST API for querying stored messages and manual cleanup
- **src/udpmonitor/udpfetch.py**: Simple Python module for programmatic access to stored messages
- **main.py**: Main application that orchestrates all services including automatic cleanup

## Notes

- The UDP listener runs in a separate thread
- The REST API runs using uvicorn ASGI server
- Automatic cleanup runs in a background daemon thread
- All database operations are thread-safe
- Binary data is stored as BLOB and displayed as hex in the API
- Text data is stored both as BLOB and as text for easier querying
- Cleanup runs at midnight local time each day
- Database is persisted in `./data/` directory when using Docker
