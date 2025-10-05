#!/usr/bin/env python3
import subprocess
import time
import os
import signal

def kill_chrome():
    """Kill existing Chrome processes"""
    try:
        subprocess.run(['pkill', '-f', 'chrome'], check=False)
        time.sleep(2)
        print("Chrome processes terminated")
    except Exception as e:
        print(f"Error killing Chrome: {e}")

def start_flask():
    """Start Flask application"""
    try:
        os.chdir('/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning')
        process = subprocess.Popen(['python3', 'run.py'])
        time.sleep(5)
        print(f"Flask application started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting Flask: {e}")
        return None

if __name__ == "__main__":
    kill_chrome()
    flask_process = start_flask()

    if flask_process:
        print("Testing environment ready")
        print("Flask running at: http://127-0-0-1.nip.io:8000")
        print("Test URL: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2")

        # Keep process running
        try:
            flask_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down Flask...")
            flask_process.terminate()