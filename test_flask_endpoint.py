#!/usr/bin/env python3
"""
Test Flask availability endpoint for Issue #4
"""

import requests
import json
import time
import subprocess
import signal
import sys
import threading
from multiprocessing import Process

class FlaskTestServer:
    def __init__(self):
        self.process = None
        self.base_url = "http://localhost:5001"
    
    def start(self):
        """Start Flask server in background"""
        print("🚀 Starting Flask test server...")
        
        def run_server():
            import os
            os.system("cd /Users/vaneeic/Source/Private/sorry-voor-de-overlast && source venv/bin/activate && python run.py")
        
        self.process = Process(target=run_server)
        self.process.start()
        
        # Wait for server to start
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/", timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ Server started successfully (attempt {attempt + 1})")
                    return True
            except:
                print(f"   ⏳ Waiting for server... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
        
        print("   ❌ Failed to start server!")
        return False
    
    def stop(self):
        """Stop Flask server"""
        if self.process:
            print("🛑 Stopping Flask test server...")
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()

def test_availability_endpoint():
    print("🧪 Test Flask Availability Endpoint - Issue #4")
    print("=" * 60)
    
    server = FlaskTestServer()
    
    try:
        # Start server
        if not server.start():
            return False
        
        # Test 1: GET request
        print("\n1. Testing GET /players/1/availability...")
        try:
            response = requests.get(f"{server.base_url}/players/1/availability", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ GET request successful")
                if 'Bea' in response.text or 'availability' in response.text.lower():
                    print("   ✅ Response contains expected content")
                else:
                    print("   ⚠️  Response content unclear:")
                    print(f"   First 200 chars: {response.text[:200]}...")
            else:
                print(f"   ❌ GET request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"   ❌ GET request exception: {e}")
            return False
        
        # Test 2: POST JSON request
        print("\n2. Testing POST /players/1/availability (JSON)...")
        json_data = {
            'updates': [
                {
                    'match_id': 1,
                    'is_available': True,
                    'notes': 'Flask endpoint test - available for match'
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
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ JSON POST successful: {result.get('message', 'No message')}")
                    if result.get('success'):
                        print("   ✅ Availability successfully saved via endpoint!")
                    else:
                        print(f"   ⚠️  Success flag: {result.get('success')}")
                except Exception as e:
                    print(f"   ⚠️  Response parsing error: {e}")
                    print(f"   Response text: {response.text}")
            else:
                print(f"   ❌ JSON POST failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ POST request exception: {e}")
            return False
        
        print("\n🎉 All Flask endpoint tests passed!")
        return True
        
    finally:
        server.stop()

if __name__ == "__main__":
    success = test_availability_endpoint()
    sys.exit(0 if success else 1)
