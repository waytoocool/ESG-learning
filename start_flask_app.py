#!/usr/bin/env python3
import subprocess
import time
import os

def main():
    # Change to the correct directory
    project_dir = '/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning'
    os.chdir(project_dir)

    print(f"Changed directory to: {os.getcwd()}")

    # Start the Flask application
    print("Starting Flask application...")
    try:
        # Use subprocess to run in background
        process = subprocess.Popen(
            ['python3', 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it time to start
        time.sleep(5)

        # Check if process is still running
        if process.poll() is None:
            print("Flask application started successfully")
            print("Application should be available at: http://127-0-0-1.nip.io:8000")
            print("Test target: http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign-data-points-v2")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"Flask failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None

    except Exception as e:
        print(f"Error starting Flask: {e}")
        return None

if __name__ == "__main__":
    main()