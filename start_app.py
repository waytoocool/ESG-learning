#!/usr/bin/env python3
import subprocess
import os
import sys

# Change to the application directory
os.chdir('/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning')

# Start the application
try:
    subprocess.run([sys.executable, 'run.py'], check=True)
except KeyboardInterrupt:
    print("Application stopped")
except Exception as e:
    print(f"Error starting application: {e}")