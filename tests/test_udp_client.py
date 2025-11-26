"""
Tests for UDP client functionality.
"""

import pytest
import socket
import time
import threading
from udpmonitor import UDPListener, MessageStorage


@pytest.fixture
def udp_listener(temp_db):
    """Create a UDP listener for testing."""
    storage, db_path = temp_db
    
    # Use a fixed port for testing (in real tests, you might want to use ephemeral ports)
    test_port = 18888
    
    listener = UDPListener(
        host='127.0.0.1',
        port=test_port,
        storage=storage
    )
    
    listener.start()
    
    # Wait a moment for listener to start
    time.sleep(0.2)
    
    yield listener, test_port, storage, db_path
    
    listener.stop()
    time.sleep(0.1)  # Give it time to stop


class TestUDPClient:
    """Tests for UDP client sending messages."""
    
    def test_send_udp_message(self, udp_listener):
        """Test sending a UDP message and receiving echo."""
        listener, port, storage, _ = udp_listener
        
        # Send message
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = b"Hello, World!"
        sock.sendto(message, ('127.0.0.1', port))
        
        # Receive echo response
        sock.settimeout(2)
        response, addr = sock.recvfrom(4096)
        sock.close()
        
        # Verify echo response
        assert response.startswith(b"ECHO:")
        assert response[5:] == message
        
        # Verify message was stored
        messages = storage.get_messages()
        assert len(messages) == 1
        assert messages[0]['data'] == message.decode('utf-8')
    
    def test_send_multiple_messages(self, udp_listener):
        """Test sending multiple UDP messages."""
        listener, port, storage, _ = udp_listener
        
        test_messages = [
            b"Message 1",
            b"Message 2",
            b"Message 3"
        ]
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        for msg in test_messages:
            sock.sendto(msg, ('127.0.0.1', port))
            time.sleep(0.1)  # Small delay between messages
        
        sock.close()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify all messages were stored
        messages = storage.get_messages()
        assert len(messages) == len(test_messages)
    
    def test_send_binary_message(self, udp_listener):
        """Test sending binary UDP message."""
        listener, port, storage, _ = udp_listener
        
        binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(binary_data, ('127.0.0.1', port))
        
        sock.settimeout(2)
        response, addr = sock.recvfrom(4096)
        sock.close()
        
        # Verify echo response
        assert response.startswith(b"ECHO:")
        assert response[5:] == binary_data
        
        # Verify binary message was stored
        messages = storage.get_messages()
        assert len(messages) == 1
        assert messages[0]['data_size'] == len(binary_data)
    
    def test_message_storage_metadata(self, udp_listener):
        """Test that message metadata is correctly stored."""
        listener, port, storage, _ = udp_listener
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = b"Test message"
        sock.sendto(message, ('127.0.0.1', port))
        sock.close()
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify metadata
        messages = storage.get_messages()
        assert len(messages) == 1
        
        msg = messages[0]
        assert msg['client_ip'] == '127.0.0.1'
        assert msg['data_size'] == len(message)
        assert 'timestamp' in msg
        assert msg['id'] > 0
    
    def test_echo_prefix(self, udp_listener):
        """Test that echo responses are prefixed with 'ECHO:'."""
        listener, port, _, _ = udp_listener
        
        test_cases = [
            b"Hello",
            b"World",
            b"Test 123",
            b"",
        ]
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        for message in test_cases:
            sock.sendto(message, ('127.0.0.1', port))
            sock.settimeout(2)
            response, _ = sock.recvfrom(4096)
            
            assert response.startswith(b"ECHO:"), f"Response should start with 'ECHO:' but got: {response}"
            assert response[5:] == message, f"Echoed data should match original"
        
        sock.close()
    
    def test_concurrent_messages(self, udp_listener):
        """Test handling concurrent UDP messages."""
        listener, port, storage, _ = udp_listener
        
        def send_message(msg_num):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = f"Concurrent message {msg_num}".encode()
            sock.sendto(message, ('127.0.0.1', port))
            sock.close()
        
        # Send multiple messages concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=send_message, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify all messages were stored
        messages = storage.get_messages()
        assert len(messages) == 10

