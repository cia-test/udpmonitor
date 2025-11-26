#!/usr/bin/env python3
"""
Production startup script using uvicorn with multiple workers.
This is the recommended way to run in production.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Start UDP Monitor in production mode with uvicorn workers'
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
        help='Number of days to retain messages (default: 1.0)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of uvicorn workers (default: 4)'
    )
    parser.add_argument(
        '--log-level',
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Logging level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Set environment variables for the subprocess
    env = os.environ.copy()
    env['UDP_HOST'] = args.udp_host
    env['UDP_PORT'] = str(args.udp_port)
    env['API_HOST'] = args.api_host
    env['API_PORT'] = str(args.api_port)
    env['DB_PATH'] = args.db_path
    env['RETENTION_DAYS'] = str(args.retention_days)
    
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    print("=" * 60)
    print("UDP Monitor - Production Mode")
    print("=" * 60)
    print(f"UDP Listener: {args.udp_host}:{args.udp_port}")
    print(f"REST API: http://{args.api_host}:{args.api_port}")
    print(f"Workers: {args.workers}")
    print(f"Database: {args.db_path}")
    print(f"Retention: {args.retention_days} days")
    print("=" * 60)
    print("\nNote: For production, run UDP listener and cleanup separately")
    print("or use the main.py script which handles everything together.")
    print("\nStarting uvicorn server...\n")
    
    # Import and create the app
    sys.path.insert(0, str(script_dir))
    from storage import MessageStorage
    from rest_api import create_app
    
    storage = MessageStorage(db_path=args.db_path)
    app = create_app(storage)
    
    # Run uvicorn
    import uvicorn
    uvicorn.run(
        app,
        host=args.api_host,
        port=args.api_port,
        workers=args.workers,
        log_level=args.log_level,
        access_log=True
    )

if __name__ == '__main__':
    main()

