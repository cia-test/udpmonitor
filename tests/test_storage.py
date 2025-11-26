"""
Tests for the storage module.
"""

import pytest
from udpmonitor import MessageStorage


class TestMessageStorage:
    """Tests for MessageStorage class."""
    
    def test_storage_initialization(self, temp_db):
        """Test storage initialization creates database schema."""
        storage, db_path = temp_db
        
        # Verify storage was initialized
        assert storage.db_path == db_path
        assert storage.lock is not None
        
        # Verify database was created
        import os
        assert os.path.exists(db_path)
    
    def test_store_message(self, temp_db):
        """Test storing a message."""
        storage, _ = temp_db
        
        message_id = storage.store_message(
            client_ip="192.168.1.100",
            client_port=54321,
            data=b"Hello, World!"
        )
        
        assert message_id > 0
    
    def test_get_messages(self, temp_db):
        """Test retrieving messages."""
        storage, _ = temp_db
        
        # Store some messages
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        
        messages = storage.get_messages()
        
        assert len(messages) == 2
        assert messages[0]['client_ip'] == "192.168.1.101"  # Most recent first
    
    def test_get_messages_with_limit(self, temp_db):
        """Test retrieving messages with limit."""
        storage, _ = temp_db
        
        # Store multiple messages
        for i in range(10):
            storage.store_message(f"192.168.1.{i}", 54321, f"Message {i}".encode())
        
        messages = storage.get_messages(limit=5)
        
        assert len(messages) == 5
    
    def test_get_messages_with_offset(self, temp_db):
        """Test retrieving messages with offset."""
        storage, _ = temp_db
        
        # Store multiple messages
        for i in range(5):
            storage.store_message(f"192.168.1.{i}", 54321, f"Message {i}".encode())
        
        messages = storage.get_messages(limit=2, offset=2)
        
        assert len(messages) == 2
    
    def test_get_messages_filter_by_ip(self, temp_db):
        """Test filtering messages by IP."""
        storage, _ = temp_db
        
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        storage.store_message("192.168.1.100", 54323, b"Message 3")
        
        messages = storage.get_messages(client_ip="192.168.1.100")
        
        assert len(messages) == 2
        assert all(msg['client_ip'] == "192.168.1.100" for msg in messages)
    
    def test_get_messages_filter_by_port(self, temp_db):
        """Test filtering messages by port."""
        storage, _ = temp_db
        
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        storage.store_message("192.168.1.102", 54321, b"Message 3")
        
        messages = storage.get_messages(client_port=54321)
        
        assert len(messages) == 2
        assert all(msg['client_port'] == 54321 for msg in messages)
    
    def test_get_message_count(self, temp_db):
        """Test getting message count."""
        storage, _ = temp_db
        
        assert storage.get_message_count() == 0
        
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        assert storage.get_message_count() == 1
        
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        assert storage.get_message_count() == 2
    
    def test_clear_messages(self, temp_db):
        """Test clearing all messages."""
        storage, _ = temp_db
        
        # Store some messages
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        
        assert storage.get_message_count() == 2
        
        storage.clear_messages()
        
        assert storage.get_message_count() == 0
    
    def test_delete_old_messages(self, temp_db):
        """Test deleting old messages."""
        storage, _ = temp_db
        
        # Store some messages
        storage.store_message("192.168.1.100", 54321, b"Message 1")
        storage.store_message("192.168.1.101", 54322, b"Message 2")
        
        # Delete messages older than 0 days (should delete all)
        deleted = storage.delete_old_messages(days=0.0)
        
        assert deleted == 2
        assert storage.get_message_count() == 0
    
    def test_binary_data_storage(self, temp_db):
        """Test storing binary data."""
        storage, _ = temp_db
        
        binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        message_id = storage.store_message("192.168.1.100", 54321, binary_data)
        
        assert message_id > 0
        
        messages = storage.get_messages()
        assert len(messages) == 1
        assert messages[0]['data_size'] == len(binary_data)
    
    def test_text_data_storage(self, temp_db):
        """Test storing text data."""
        storage, _ = temp_db
        
        text_data = b"Hello, World!"
        storage.store_message("192.168.1.100", 54321, text_data)
        
        messages = storage.get_messages()
        assert len(messages) == 1
        assert messages[0]['data'] == text_data.decode('utf-8')

