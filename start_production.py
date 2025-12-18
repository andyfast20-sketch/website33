"""
Production Server Startup Script
=================================
Runs the server with optimized settings for handling concurrent calls.

Usage: python start_production.py
"""
import os
import subprocess
import sys

# Set production environment variable
os.environ["PRODUCTION"] = "true"

# Get Python executable path
python_exe = sys.executable

# Run with 4 workers for better concurrent handling
# Workers = (2 x CPU cores) + 1 is a good rule of thumb
# Adjust --workers based on your CPU cores
cmd = [
    python_exe,
    "-m",
    "uvicorn",
    "vonage_agent:app",
    "--host", "0.0.0.0",
    "--port", "5004",
    "--workers", "4",  # Adjust based on your CPU cores
    "--limit-concurrency", "20",  # Max 20 concurrent connections
    "--timeout-keep-alive", "65"
]

print("🚀 Starting production server with 4 workers...")
print(f"📊 Max concurrent connections: 20")
print(f"⚡ Production mode enabled (reduced logging)")
print(f"🌐 Server will be available at http://0.0.0.0:5004")
print("-" * 60)

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n✅ Server stopped")
