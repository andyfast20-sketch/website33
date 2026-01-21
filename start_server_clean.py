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
from datetime import datetime

def kill_process_on_port(port=5004):
    """Kill any process using the specified port."""
    print(f"🔍 Checking for processes on port {port}...")
    
    try:
        # Get the process ID using the port
        result = subprocess.run(
            [
                "powershell", "-Command",
                f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue).OwningProcess"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            raw_pids = [ln.strip() for ln in result.stdout.strip().split('\n') if ln.strip()]
            unique_pids = sorted({pid for pid in raw_pids if pid.isdigit() and int(pid) > 0}, key=int)
            for pid in unique_pids:
                print(f"⚠️  Found process {pid} listening on port {port}")
                subprocess.run(
                    ["powershell", "-Command", f"Stop-Process -Id {pid} -Force"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                print(f"✅ Killed process {pid}")
                time.sleep(1)
        else:
            # Fallback: netstat/taskkill (works even when Get-NetTCPConnection is unavailable)
            try:
                netstat = subprocess.run(
                    ["cmd", "/c", f"netstat -ano | findstr :{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                lines = [ln.strip() for ln in (netstat.stdout or "").splitlines() if ln.strip()]
                pids = set()
                for ln in lines:
                    parts = ln.split()
                    if len(parts) >= 5 and parts[-1].isdigit():
                        pids.add(parts[-1])
                if pids:
                    for pid in sorted(pids):
                        if pid == "0":
                            continue
                        print(f"⚠️  Found process {pid} on port {port} (netstat)")
                        subprocess.run(
                            ["cmd", "/c", f"taskkill /PID {pid} /F"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        print(f"✅ Killed process {pid}")
                        time.sleep(1)
                else:
                    print(f"✅ Port {port} is free")
            except subprocess.TimeoutExpired:
                print("⚠️  Timeout checking port with netstat - continuing anyway")
            except Exception as e:
                print(f"⚠️  Error checking port with netstat: {e}")
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
        # Start the server in a detached process so this script can exit.
        log_path = os.path.join(os.getcwd(), "server_log_new.txt")

        # If an old log exists with a UTF-16 BOM (common when created via PowerShell redirection),
        # rotate it so we don't append UTF-8 into a UTF-16 file (which corrupts the log output).
        try:
            if os.path.exists(log_path):
                with open(log_path, "rb") as f:
                    head = f.read(4)
                if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rotated = os.path.join(os.getcwd(), f"server_log_new.{ts}.utf16.bak.txt")
                    os.replace(log_path, rotated)
                    print(f"📝 Rotated UTF-16 log to: {rotated}")
        except Exception:
            pass

        # Start fresh UTF-8 log each run so tailing/grep works reliably.
        log_file = open(log_path, "w", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, "vonage_agent.py"],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        print(f"✅ Server started (PID: {proc.pid})")
        print(f"📝 Logging to: {log_path}")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
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
