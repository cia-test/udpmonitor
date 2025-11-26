"""
Storage module for UDP messages.
Uses SQLite to store datagrams with connection information.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading


class MessageStorage:
    """Thread-safe storage for UDP messages using SQLite."""
    
    def __init__(self, db_path: str = "udpmonitor.db"):
        """
        Initialize the storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    client_ip TEXT NOT NULL,
                    client_port INTEGER NOT NULL,
                    data BLOB NOT NULL,
                    data_text TEXT,
                    data_size INTEGER NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON messages(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_client 
                ON messages(client_ip, client_port)
            """)
            conn.commit()
            conn.close()
    
    def store_message(self, client_ip: str, client_port: int, data: bytes) -> int:
        """
        Store a UDP message.
        
        Args:
            client_ip: IP address of the client
            client_port: Port of the client
            data: The message data as bytes
            
        Returns:
            The ID of the stored message
        """
        timestamp = datetime.utcnow().isoformat()
        data_size = len(data)
        
        # Try to decode as text for easier querying
        try:
            data_text = data.decode('utf-8')
        except UnicodeDecodeError:
            data_text = None
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages 
                (timestamp, client_ip, client_port, data, data_text, data_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, client_ip, client_port, data, data_text, data_size))
            message_id = cursor.lastrowid
            conn.commit()
            conn.close()
        
        return message_id
    
    def get_messages(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        client_ip: Optional[str] = None,
        client_port: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve stored messages.
        
        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            client_ip: Filter by client IP (optional)
            client_port: Filter by client port (optional)
            
        Returns:
            List of message dictionaries
        """
        query = "SELECT id, timestamp, client_ip, client_port, data, data_text, data_size FROM messages"
        params = []
        conditions = []
        
        if client_ip:
            conditions.append("client_ip = ?")
            params.append(client_ip)
        
        if client_port:
            conditions.append("client_port = ?")
            params.append(client_port)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        if offset:
            query += " OFFSET ?"
            params.append(offset)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
        
        messages = []
        for row in rows:
            # Try to decode data as text, fallback to base64 for binary
            data = row['data']
            try:
                if row['data_text']:
                    data_repr = row['data_text']
                else:
                    data_repr = data.hex()
            except:
                data_repr = data.hex()
            
            messages.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'client_ip': row['client_ip'],
                'client_port': row['client_port'],
                'data': data_repr,
                'data_size': row['data_size']
            })
        
        return messages
    
    def get_message_count(self) -> int:
        """Get the total number of stored messages."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            conn.close()
        return count
    
    def clear_messages(self):
        """Clear all stored messages."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()
            conn.close()
    
    def delete_old_messages(self, days: float = 1.0) -> int:
        """
        Delete messages older than the specified number of days.
        
        Args:
            days: Number of days to retain messages (default: 1.0)
            
        Returns:
            Number of messages deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        cutoff_timestamp = cutoff_time.isoformat()
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Count messages to be deleted
            cursor.execute("SELECT COUNT(*) FROM messages WHERE timestamp < ?", (cutoff_timestamp,))
            count = cursor.fetchone()[0]
            # Delete old messages
            cursor.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_timestamp,))
            conn.commit()
            conn.close()
        
        return count

