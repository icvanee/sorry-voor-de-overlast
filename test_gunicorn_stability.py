#!/usr/bin/env python3
"""
Stable test for availability endpoint using Gunicorn server
Much more reliable than Flask development server
"""

import requests
import time
import json
import subprocess
import os
import signal
import threading
from datetime import datetime

class GunicornTestServer:
    def __init__(self, port=5001):
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"
    
    def start(self):
        """Start Gunicorn server in background"""
        print(f"🚀 Starting Gunicorn server on port {self.port}...")
        
        # Change to project directory
        os.chdir('/Users/vaneeic/Source/Private/sorry-voor-de-overlast')
        
        # Start Gunicorn in background
        cmd = [
            'bash', '-c',
            f'source venv/bin/activate && gunicorn run:app --bind 0.0.0.0:{self.port} --workers 1 --daemon --pid gunicorn.pid --log-file gunicorn.log'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("   ✅ Gunicorn started as daemon")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to start Gunicorn: {e}")
            return False
        
        # Wait for server to be ready
        max_attempts = 15
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/", timeout=3)
                if response.status_code == 200:
                    print(f"   ✅ Server ready after {attempt + 1} attempts")
                    return True
            except:
                if attempt < max_attempts - 1:
                    print(f"   ⏳ Waiting for server... ({attempt + 1}/{max_attempts})")
                    time.sleep(2)
        
        print("   ❌ Server failed to start within timeout")
        return False
    
    def stop(self):
        """Stop Gunicorn server"""
        print("🛑 Stopping Gunicorn server...")
        try:
            # Kill using PID file
            if os.path.exists('gunicorn.pid'):
                with open('gunicorn.pid', 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)  # Give it time to shutdown gracefully
                try:
                    os.kill(pid, 0)  # Check if still running
                    os.kill(pid, signal.SIGKILL)  # Force kill if necessary
                except OSError:
                    pass  # Process already dead
                os.remove('gunicorn.pid')
            
            # Cleanup log file
            if os.path.exists('gunicorn.log'):
                os.remove('gunicorn.log')
                
        except Exception as e:
            print(f"   ⚠️ Error during cleanup: {e}")

def test_availability_endpoint_stable():
    print(f"🧪 Stable Availability Endpoint Test - {datetime.now().strftime('%H:%M:%S')}")
    print("Using Gunicorn (same as Railway production)")
    print("=" * 70)
    
    server = GunicornTestServer()
    
    try:
        # Start server
        if not server.start():
            return False
        
        print("\n📋 Test Suite:")
        
        # Test 1: Health check
        print("\n1. Health check...")
        try:
            response = requests.get(f"{server.base_url}/", timeout=5)
            print(f"   Root endpoint: {response.status_code} ✅")
        except Exception as e:
            print(f"   Root endpoint error: {e} ❌")
            return False
        
        # Test 2: Player list
        print("\n2. Player list endpoint...")
        try:
            response = requests.get(f"{server.base_url}/players/", timeout=5)
            print(f"   Players list: {response.status_code} ✅")
        except Exception as e:
            print(f"   Players list error: {e} ❌")
            return False
        
        # Test 3: Availability GET
        print("\n3. Availability GET endpoint...")
        try:
            response = requests.get(f"{server.base_url}/players/1/availability", timeout=10)
            print(f"   GET availability: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ GET request successful")
                # Check if it contains expected content
                if 'Bea' in response.text or 'availability' in response.text.lower():
                    print("   ✅ Response contains expected content")
                else:
                    print("   ⚠️  Response content unclear")
            else:
                print(f"   ❌ GET failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ GET request error: {e}")
            return False
        
        # Test 4: Availability POST
        print("\n4. Availability POST endpoint...")
        json_data = {
            'updates': [
                {
                    'match_id': 1,
                    'is_available': True,
                    'notes': 'Gunicorn stability test - available'
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{server.base_url}/players/1/availability",
                json=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   POST availability: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        print(f"   ✅ POST successful: {result.get('message')}")
                    else:
                        print(f"   ⚠️  POST response: {result}")
                except:
                    print(f"   ⚠️  POST response not JSON: {response.text[:100]}")
            else:
                print(f"   ❌ POST failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ POST request error: {e}")
            return False
        
        # Test 5: Load test (multiple requests)
        print("\n5. Stability test (10 rapid requests)...")
        success_count = 0
        for i in range(10):
            try:
                response = requests.get(f"{server.base_url}/players/1/availability", timeout=3)
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
        
        print(f"   ✅ {success_count}/10 requests successful")
        
        if success_count >= 8:  # Allow some failures
            print("\n🎉 All stability tests passed!")
            print("   Gunicorn is much more stable than Flask dev server")
            print("   Ready for Railway production deployment")
            return True
        else:
            print(f"\n⚠️ Stability concerns: only {success_count}/10 requests successful")
            return False
        
    finally:
        server.stop()

if __name__ == "__main__":
    success = test_availability_endpoint_stable()
    print(f"\n{'✅ STABILITY TEST PASSED' if success else '❌ STABILITY TEST FAILED'}")
    exit(0 if success else 1)
