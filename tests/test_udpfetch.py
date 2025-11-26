"""
Tests for the udpfetch module.
"""

import pytest
from udpmonitor import udpfetch
from udpmonitor.udpfetch import Message


class TestMessage:
    """Tests for the Message dataclass."""
    
    def test_message_creation(self):
        """Test creating a Message object."""
        msg = Message(
            id=1,
            timestamp="2024-01-01T12:00:00",
            ip="192.168.1.100",
            port=54321,
            message="Hello, World!",
            data=b"Hello, World!",
            data_size=13
        )
        
        assert msg.id == 1
        assert msg.ip == "192.168.1.100"
        assert msg.port == 54321
        assert msg.message == "Hello, World!"
        assert msg.data == b"Hello, World!"
        assert msg.data_size == 13
    
    def test_message_repr(self):
        """Test Message string representation."""
        msg = Message(
            id=1,
            timestamp="2024-01-01T12:00:00",
            ip="192.168.1.100",
            port=54321,
            message="Hello, World!",
            data=b"Hello, World!",
            data_size=13
        )
        
        repr_str = repr(msg)
        assert "Message" in repr_str
        assert "id=1" in repr_str
        assert "192.168.1.100" in repr_str


class TestUDPFetch:
    """Tests for udpfetch functions."""
    
    def test_get_messages_empty_db(self, temp_db):
        """Test getting messages from an empty database."""
        _, db_path = temp_db
        
        messages = udpfetch.get_messages(db_path=db_path)
        assert messages == []
    
    def test_get_messages_with_data(self, sample_messages):
        """Test getting messages from a database with data."""
        _, db_path, expected_messages = sample_messages
        
        messages = udpfetch.get_messages(db_path=db_path)
        
        assert len(messages) == 4
        assert all(isinstance(msg, Message) for msg in messages)
        # Most recent message should be the last one stored
        assert messages[0].ip == expected_messages[-1][0]  # Last message in list
        assert messages[0].port == expected_messages[-1][1]
    
    def test_get_messages_with_limit(self, sample_messages):
        """Test getting messages with a limit."""
        _, db_path, _ = sample_messages
        
        messages = udpfetch.get_messages(limit=2, db_path=db_path)
        
        assert len(messages) == 2
    
    def test_get_messages_filter_by_ip(self, sample_messages):
        """Test filtering messages by IP address."""
        _, db_path, _ = sample_messages
        
        messages = udpfetch.get_messages(client_ip="192.168.1.100", db_path=db_path)
        
        assert len(messages) == 1
        assert messages[0].ip == "192.168.1.100"
        assert messages[0].port == 54321
    
    def test_get_messages_filter_by_port(self, sample_messages):
        """Test filtering messages by port."""
        _, db_path, _ = sample_messages
        
        messages = udpfetch.get_messages(client_port=54322, db_path=db_path)
        
        assert len(messages) == 1
        assert messages[0].port == 54322
    
    def test_get_messages_filter_by_ip_and_port(self, sample_messages):
        """Test filtering messages by both IP and port."""
        _, db_path, _ = sample_messages
        
        messages = udpfetch.get_messages(
            client_ip="192.168.1.101",
            client_port=54322,
            db_path=db_path
        )
        
        assert len(messages) == 1
        assert messages[0].ip == "192.168.1.101"
        assert messages[0].port == 54322
    
    def test_get_message_count_empty(self, temp_db):
        """Test getting message count from empty database."""
        _, db_path = temp_db
        
        count = udpfetch.get_message_count(db_path=db_path)
        assert count == 0
    
    def test_get_message_count_with_data(self, sample_messages):
        """Test getting message count from database with data."""
        _, db_path, _ = sample_messages
        
        count = udpfetch.get_message_count(db_path=db_path)
        assert count == 4
    
    def test_get_latest_message_empty(self, temp_db):
        """Test getting latest message from empty database."""
        _, db_path = temp_db
        
        latest = udpfetch.get_latest_message(db_path=db_path)
        assert latest is None
    
    def test_get_latest_message_with_data(self, sample_messages):
        """Test getting latest message from database with data."""
        _, db_path, expected_messages = sample_messages
        
        latest = udpfetch.get_latest_message(db_path=db_path)
        
        assert latest is not None
        assert isinstance(latest, Message)
        # Most recent message should be the last one stored
        assert latest.ip == expected_messages[-1][0]  # Last message in list
        assert latest.port == expected_messages[-1][1]
    
    def test_message_attributes(self, sample_messages):
        """Test accessing message attributes."""
        _, db_path, _ = sample_messages
        
        messages = udpfetch.get_messages(limit=1, db_path=db_path)
        
        assert len(messages) == 1
        msg = messages[0]
        
        # Test all attributes are accessible
        assert hasattr(msg, 'id')
        assert hasattr(msg, 'timestamp')
        assert hasattr(msg, 'ip')
        assert hasattr(msg, 'port')
        assert hasattr(msg, 'message')
        assert hasattr(msg, 'data')
        assert hasattr(msg, 'data_size')
        
        # Test attribute types
        assert isinstance(msg.id, int)
        assert isinstance(msg.timestamp, str)
        assert isinstance(msg.ip, str)
        assert isinstance(msg.port, int)
        assert isinstance(msg.message, str)
        assert isinstance(msg.data, bytes)
        assert isinstance(msg.data_size, int)
    
    def test_binary_message_handling(self, temp_db):
        """Test handling of binary messages."""
        storage, db_path = temp_db
        
        # Store a binary message
        binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        storage.store_message("192.168.1.100", 54321, binary_data)
        
        messages = udpfetch.get_messages(db_path=db_path)
        
        assert len(messages) == 1
        assert messages[0].data == binary_data
        # Binary data should be represented as hex
        assert isinstance(messages[0].message, str)

