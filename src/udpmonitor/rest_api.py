"""
REST API for querying stored UDP messages.
Production-ready FastAPI application with uvicorn.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from .storage import MessageStorage
import logging

logger = logging.getLogger(__name__)


def create_app(storage: MessageStorage) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        storage: MessageStorage instance to use
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="UDP Monitor API",
        description="REST API for querying stored UDP messages",
        version="1.0.0"
    )
    
    # Add CORS middleware for production use
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/messages", response_model=dict)
    async def get_messages(
        limit: Optional[int] = Query(default=100, ge=1, le=1000, description="Maximum number of messages to return"),
        offset: Optional[int] = Query(default=0, ge=0, description="Number of messages to skip"),
        client_ip: Optional[str] = Query(default=None, description="Filter by client IP address"),
        client_port: Optional[int] = Query(default=None, ge=1, le=65535, description="Filter by client port")
    ):
        """
        GET endpoint to retrieve stored messages.
        
        Returns messages with optional filtering and pagination.
        """
        try:
            messages = storage.get_messages(
                limit=limit,
                offset=offset,
                client_ip=client_ip,
                client_port=client_port
            )
            
            return {
                'success': True,
                'count': len(messages),
                'messages': messages
            }
        
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/messages/count", response_model=dict)
    async def get_message_count():
        """GET endpoint to retrieve the total count of stored messages."""
        try:
            count = storage.get_message_count()
            return {
                'success': True,
                'count': count
            }
        except Exception as e:
            logger.error(f"Error getting message count: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/messages/{message_id}", response_model=dict)
    async def get_message(message_id: int):
        """GET endpoint to retrieve a specific message by ID."""
        try:
            # Query database directly for better performance
            import sqlite3
            with storage.lock:
                conn = sqlite3.connect(storage.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, client_ip, client_port, data, data_text, data_size FROM messages WHERE id = ?",
                    (message_id,)
                )
                row = cursor.fetchone()
                conn.close()
            
            if row:
                # Format message like storage.get_messages does
                if row['data_text']:
                    message_text = row['data_text']
                else:
                    try:
                        message_text = row['data'].decode('utf-8', errors='replace')
                    except:
                        message_text = row['data'].hex()
                
                message = {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'client_ip': row['client_ip'],
                    'client_port': row['client_port'],
                    'data': message_text,
                    'data_size': row['data_size']
                }
                
                return {
                    'success': True,
                    'message': message
                }
            else:
                raise HTTPException(status_code=404, detail='Message not found')
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving message {message_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health", response_model=dict)
    async def health():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'service': 'udpmonitor'
        }
    
    @app.post("/cleanup", response_model=dict)
    async def cleanup(
        days: Optional[float] = Query(default=1.0, ge=0.0, description="Number of days to retain")
    ):
        """
        POST endpoint to manually trigger cleanup of old messages.
        
        Deletes messages older than the specified number of days.
        """
        try:
            deleted_count = storage.delete_old_messages(days=days)
            
            logger.info(f"Cleanup completed: deleted {deleted_count} messages older than {days} day(s)")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': days
            }
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

