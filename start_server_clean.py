"""
Clean Server Startup Script
============================
Kills any existing server instances on port 5004 before starting fresh.
This prevents the erratic behavior caused by stale server processes.

Usage:
    python start_server_clean.py
"""

import subprocess
import sys
import time
import os

def kill_process_on_port(port=5004):
    """Kill any process using the specified port."""
    print(f"🔍 Checking for processes on port {port}...")
    
    try:
        # Get the process ID using the port
        result = subprocess.run(
            [
                "powershell", "-Command",
                f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                pid = pid.strip()
                if pid and pid.isdigit() and int(pid) > 0:
                    print(f"⚠️  Found process {pid} on port {port}")
                    # Kill the process
                    subprocess.run(
                        ["powershell", "-Command", f"Stop-Process -Id {pid} -Force"],
                        capture_output=True,
                        timeout=5
                    )
                    print(f"✅ Killed process {pid}")
                    time.sleep(1)
        else:
            print(f"✅ Port {port} is free")
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout checking port - continuing anyway")
    except Exception as e:
        print(f"⚠️  Error checking port: {e}")

def start_server():
    """Start the Vonage agent server."""
    print("\n🚀 Starting Vonage Voice Agent...")
    print("=" * 70)
    
    # Set unbuffered output
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    try:
        # Start the server (this will run until Ctrl+C)
        subprocess.run(
            [sys.executable, "vonage_agent.py"],
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server exited with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("  VONAGE VOICE AGENT - CLEAN STARTUP")
    print("=" * 70)
    
    # Kill any existing instances
    kill_process_on_port(5004)
    
    # Small delay to ensure port is fully released
    time.sleep(2)
    
    # Start fresh server
    start_server()
