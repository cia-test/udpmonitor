"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from udpmonitor import MessageStorage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    storage = MessageStorage(db_path=db_path)
    
    yield storage, db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_messages(temp_db):
    """Create sample messages in the database."""
    import time
    storage, db_path = temp_db
    
    # Add some test messages with small delays to ensure different timestamps
    messages = [
        ("192.168.1.100", 54321, b"Hello, World!"),
        ("192.168.1.101", 54322, b"Test message 1"),
        ("192.168.1.102", 54323, b"Test message 2"),
        ("10.0.0.1", 12345, b"Binary test: \x00\x01\x02\x03"),
    ]
    
    for ip, port, data in messages:
        storage.store_message(ip, port, data)
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    return storage, db_path, messages

