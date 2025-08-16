#!/usr/bin/env python3
"""
Minimal test for Issue #4
Just test if the availability endpoint is accessible
"""

import sys
import time
import os
import signal
import subprocess
import requests
from datetime import datetime

def test_simple():
    print(f"🧪 Minimal Flask Availability Test - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Start server in background
    print("1. Starting server...")
    server_process = subprocess.Popen([
        'bash', '-c', 
        'cd /Users/vaneeic/Source/Private/sorry-voor-de-overlast && source venv/bin/activate && python run.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    
    # Wait a bit for server to start
    time.sleep(5)
    
    try:
        # Test basic connectivity
        print("2. Testing server connectivity...")
        try:
            response = requests.get("http://localhost:5001/", timeout=5)
            print(f"   Root endpoint status: {response.status_code}")
        except Exception as e:
            print(f"   Root endpoint error: {e}")
            return False
        
        # Test availability endpoint
        print("3. Testing availability endpoint...")
        try:
            response = requests.get("http://localhost:5001/players/1/availability", timeout=10)
            print(f"   Availability endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ GET request successful!")
                
                # Test POST as well
                print("4. Testing POST request...")
                json_data = {
                    'updates': [
                        {
                            'match_id': 1,
                            'is_available': True,
                            'notes': 'Simple test'
                        }
                    ]
                }
                
                post_response = requests.post(
                    "http://localhost:5001/players/1/availability",
                    json=json_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f"   POST status: {post_response.status_code}")
                
                if post_response.status_code == 200:
                    try:
                        result = post_response.json()
                        print(f"   ✅ POST successful: {result}")
                        return True
                    except:
                        print(f"   ⚠️  POST response not JSON: {post_response.text[:100]}")
                        return False
                else:
                    print(f"   ❌ POST failed: {post_response.text[:100]}")
                    return False
            else:
                print(f"   ❌ GET failed with status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        
        except Exception as e:
            print(f"   ❌ Availability endpoint error: {e}")
            return False
    
    finally:
        # Kill server
        print("5. Stopping server...")
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            server_process.wait(timeout=5)
        except:
            try:
                os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
            except:
                pass

if __name__ == "__main__":
    success = test_simple()
    print(f"\n{'✅ Test PASSED' if success else '❌ Test FAILED'}")
    sys.exit(0 if success else 1)
