#!/usr/bin/env python3
"""
Production-like local server using Gunicorn
Much more stable than Flask development server
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

def start_gunicorn_server():
    """Start Gunicorn server for local development"""
    print("🚀 Starting Gunicorn server (production-like)...")
    print("   More stable than Flask development server")
    print("   Same setup as Railway production environment")
    print("")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Activate virtual environment and start Gunicorn
    cmd = [
        'bash', '-c',
        'source venv/bin/activate && gunicorn run:app --bind 0.0.0.0:5001 --workers 2 --reload --log-level info'
    ]
    
    print("Command: gunicorn run:app --bind 0.0.0.0:5001 --workers 2 --reload --log-level info")
    print("URL: http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Start Gunicorn
        process = subprocess.run(cmd, check=False)
        return process.returncode
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0

if __name__ == "__main__":
    exit_code = start_gunicorn_server()
    sys.exit(exit_code)
