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

# Run with SINGLE WORKER but high concurrency
# WebSocket apps need shared state, so we use 1 worker with threading
# Uvicorn handles concurrent connections efficiently with async/await
cmd = [
    python_exe,
    "-m",
    "uvicorn",
    "vonage_agent:app",
    "--host", "0.0.0.0",
    "--port", "5004",
    "--workers", "1",  # MUST be 1 for WebSocket state management
    "--limit-concurrency", "100",  # Can handle up to 100 concurrent calls
    "--timeout-keep-alive", "65",
    "--ws-max-size", "16777216",  # 16MB max WebSocket message size
    "--backlog", "2048"  # Queue up to 2048 pending connections
]

print("🚀 Starting production server...")
print(f"📊 Max concurrent connections: 100")
print(f"🔌 WebSocket-optimized (single worker with async)")
print(f"⚡ Production mode enabled (reduced logging)")
print(f"🌐 Server will be available at http://0.0.0.0:5004")
print("-" * 60)

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n✅ Server stopped")
