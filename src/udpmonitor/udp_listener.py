"""
UDP Listener that receives datagrams, echoes them back with "ECHO:" prefix,
and stores them in the database.
"""

import socket
import threading
from typing import Optional
from .storage import MessageStorage


class UDPListener:
    """UDP listener that echoes messages and stores them."""
    
    def __init__(
        self, 
        host: str = '0.0.0.0',
        port: int = 8888,
        storage: Optional[MessageStorage] = None
    ):
        """
        Initialize the UDP listener.
        
        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to listen on
            storage: MessageStorage instance for storing messages
        """
        self.host = host
        self.port = port
        self.storage = storage or MessageStorage()
        self.sock = None
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the UDP listener in a separate thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"UDP Listener started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the UDP listener."""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=2)
        print("UDP Listener stopped")
    
    def _run(self):
        """Main loop for receiving and processing UDP messages."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            
            print(f"UDP Listener listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    # Receive datagram
                    data, addr = self.sock.recvfrom(4096)
                    client_ip, client_port = addr
                    
                    # Store the message
                    message_id = self.storage.store_message(
                        client_ip=client_ip,
                        client_port=client_port,
                        data=data
                    )
                    
                    # Prepare echo response with "ECHO:" prefix
                    echo_prefix = b"ECHO:"
                    echo_response = echo_prefix + data
                    
                    # Send echo response
                    self.sock.sendto(echo_response, addr)
                    
                    # Log the activity
                    try:
                        data_preview = data.decode('utf-8')[:50]
                        if len(data) > 50:
                            data_preview += "..."
                    except UnicodeDecodeError:
                        data_preview = f"<binary: {len(data)} bytes>"
                    
                    print(f"[{message_id}] Received from {client_ip}:{client_port}: {data_preview}")
                    print(f"[{message_id}] Echoed back with ECHO: prefix")
                    
                except socket.error as e:
                    if self.running:
                        print(f"Socket error: {e}")
                    break
                except Exception as e:
                    print(f"Error processing message: {e}")
        
        except Exception as e:
            print(f"UDP Listener error: {e}")
        finally:
            if self.sock:
                self.sock.close()

