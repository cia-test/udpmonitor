#!/usr/bin/env python3
"""
Main entry point for UDP Monitor.
Production-ready with uvicorn ASGI server.
"""

import argparse
import signal
import sys
import threading
import time
import logging
from datetime import datetime, timedelta
from src.udpmonitor import MessageStorage, UDPListener, create_app
import uvicorn


class UDPMonitor:
    """Main application class that manages UDP listener and REST API."""
    
    def __init__(
        self,
        udp_host: str = '0.0.0.0',
        udp_port: int = 8888,
        api_host: str = '0.0.0.0',
        api_port: int = 5000,
        db_path: str = 'udpmonitor.db',
        retention_days: float = 1.0
    ):
        """
        Initialize the UDP Monitor application.
        
        Args:
            udp_host: Host for UDP listener
            udp_port: Port for UDP listener
            api_host: Host for REST API
            api_port: Port for REST API
            db_path: Path to SQLite database
            retention_days: Number of days to retain messages (default: 1.0)
        """
        self.storage = MessageStorage(db_path=db_path)
        self.udp_listener = UDPListener(
            host=udp_host,
            port=udp_port,
            storage=self.storage
        )
        self.app = create_app(self.storage)
        self.api_host = api_host
        self.api_port = api_port
        self.retention_days = retention_days
        self.running = False
        self.cleanup_thread = None
    
    def _cleanup_worker(self):
        """Background worker that runs nightly cleanup."""
        while self.running:
            try:
                # Calculate time until next midnight
                now = datetime.now()
                # Try today's midnight first
                today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # If today's midnight is in the past, use tomorrow's midnight
                if today_midnight <= now:
                    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    next_midnight = today_midnight
                
                sleep_seconds = (next_midnight - now).total_seconds()
                
                # Sleep until midnight
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                
                if not self.running:
                    break
                
                # Run cleanup
                deleted_count = self.storage.delete_old_messages(days=self.retention_days)
                if deleted_count > 0:
                    print(f"[Cleanup] Deleted {deleted_count} messages older than {self.retention_days} day(s)")
                else:
                    print(f"[Cleanup] No messages older than {self.retention_days} day(s) to delete")
                
            except Exception as e:
                print(f"[Cleanup] Error during cleanup: {e}")
                # If there's an error, wait 1 hour before retrying
                time.sleep(3600)
    
    def start(self):
        """Start both the UDP listener and REST API."""
        print("=" * 60)
        print("UDP Monitor System")
        print("=" * 60)
        
        # Start UDP listener
        self.udp_listener.start()
        
        # Start cleanup thread
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        print(f"Database cleanup scheduled: nightly deletion of messages older than {self.retention_days} day(s)")
        
        # Start REST API with uvicorn
        print(f"REST API starting on http://{self.api_host}:{self.api_port}")
        print(f"  - GET /messages - Retrieve stored messages")
        print(f"  - GET /messages/count - Get message count")
        print(f"  - GET /messages/{{id}} - Get specific message")
        print(f"  - GET /health - Health check")
        print(f"  - POST /cleanup - Manual cleanup")
        print(f"  - API docs: http://{self.api_host}:{self.api_port}/docs")
        print("=" * 60)
        
        # Run uvicorn ASGI server
        config = uvicorn.Config(
            app=self.app,
            host=self.api_host,
            port=self.api_port,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        
        try:
            server.run()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop both services."""
        if not self.running:
            return
        
        print("\nShutting down...")
        self.running = False
        self.udp_listener.stop()
        print("UDP Monitor stopped")


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='UDP Monitor - UDP listener with REST API (Production-ready)'
    )
    parser.add_argument(
        '--udp-host',
        default='0.0.0.0',
        help='Host for UDP listener (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--udp-port',
        type=int,
        default=8888,
        help='Port for UDP listener (default: 8888)'
    )
    parser.add_argument(
        '--api-host',
        default='0.0.0.0',
        help='Host for REST API (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=5000,
        help='Port for REST API (default: 5000)'
    )
    parser.add_argument(
        '--db-path',
        default='udpmonitor.db',
        help='Path to SQLite database file (default: udpmonitor.db)'
    )
    parser.add_argument(
        '--retention-days',
        type=float,
        default=1.0,
        help='Number of days to retain messages before deletion (default: 1.0)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of uvicorn workers (default: 1, use 4+ for production)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    monitor = UDPMonitor(
        udp_host=args.udp_host,
        udp_port=args.udp_port,
        api_host=args.api_host,
        api_port=args.api_port,
        db_path=args.db_path,
        retention_days=args.retention_days
    )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor.start()


if __name__ == '__main__':
    main()
