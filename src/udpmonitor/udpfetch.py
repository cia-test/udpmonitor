"""
Simple module to fetch UDP messages from the udpmonitor database.
"""

import sqlite3
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Message object with easy-to-access attributes."""
    id: int
    timestamp: str
    ip: str
    port: int
    message: str
    data: bytes
    data_size: int
    
    def __repr__(self):
        return f"Message(id={self.id}, ip={self.ip}, port={self.port}, message={self.message[:50] if len(self.message) > 50 else self.message}...)"


def get_messages(
    limit: Optional[int] = None,
    db_path: str = "udpmonitor.db",
    client_ip: Optional[str] = None,
    client_port: Optional[int] = None
) -> List[Message]:
    """
    Retrieve messages from the udpmonitor database.
    
    Args:
        limit: Maximum number of messages to return (default: None, returns all)
        db_path: Path to SQLite database file (default: udpmonitor.db)
        client_ip: Filter by client IP address (optional)
        client_port: Filter by client port (optional)
    
    Returns:
        List of Message objects with attributes: id, timestamp, ip, port, message, data, data_size
    
    Example:
        >>> from udpmonitor import udpfetch
        >>> messages = udpfetch.get_messages(limit=10)
        >>> print(messages[0].ip)
        '192.168.1.100'
        >>> print(messages[0].port)
        54321
        >>> print(messages[0].message)
        'Hello, World!'
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
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        # Use data_text if available, otherwise decode data or use hex representation
        if row['data_text']:
            message_text = row['data_text']
        else:
            try:
                message_text = row['data'].decode('utf-8', errors='replace')
            except:
                message_text = row['data'].hex()
        
        messages.append(Message(
            id=row['id'],
            timestamp=row['timestamp'],
            ip=row['client_ip'],
            port=row['client_port'],
            message=message_text,
            data=row['data'],
            data_size=row['data_size']
        ))
    
    return messages


def get_message_count(db_path: str = "udpmonitor.db") -> int:
    """
    Get the total number of stored messages.
    
    Args:
        db_path: Path to SQLite database file (default: udpmonitor.db)
    
    Returns:
        Total count of messages
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_latest_message(db_path: str = "udpmonitor.db") -> Optional[Message]:
    """
    Get the most recent message.
    
    Args:
        db_path: Path to SQLite database file (default: udpmonitor.db)
    
    Returns:
        Most recent Message object, or None if no messages exist
    """
    messages = get_messages(limit=1, db_path=db_path)
    return messages[0] if messages else None

