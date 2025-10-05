import subprocess
import time
import os

# Kill Chrome processes
print("Killing Chrome processes...")
subprocess.run(['pkill', '-f', 'chrome'], check=False)
time.sleep(2)

# Kill Python/Flask processes
print("Killing Python/Flask processes...")
subprocess.run(['pkill', '-f', 'python3 run.py'], check=False)
time.sleep(2)

print("Cleanup complete")