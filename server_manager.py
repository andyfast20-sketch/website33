"""
Server Manager for Vonage Agent
================================
Manage the server: start, stop, restart, check status

Run this file to control your server easily.
"""

import subprocess
import psutil
import os
import sys
import time

SERVER_SCRIPT = "vonage_agent.py"
SERVER_PORT = 5004

def get_pid_on_port(port):
    """Find process ID using the specified port"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections'] or []:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def is_server_running():
    """Check if server is running on port 5004"""
    pid = get_pid_on_port(SERVER_PORT)
    return pid is not None, pid

def start_server():
    """Start the server"""
    running, pid = is_server_running()
    if running:
        print(f"❌ Server is already running (PID: {pid})")
        return False
    
    print("🚀 Starting server...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, SERVER_SCRIPT)
    
    # Start server in a new console window
    subprocess.Popen(
        [sys.executable, script_path],
        cwd=script_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Wait a moment and check if it started
    time.sleep(2)
    running, pid = is_server_running()
    if running:
        print(f"✅ Server started successfully (PID: {pid})")
        print(f"🌐 Server running at http://localhost:{SERVER_PORT}")
        return True
    else:
        print("❌ Failed to start server")
        return False

def stop_server():
    """Stop the server"""
    running, pid = is_server_running()
    if not running:
        print("❌ Server is not running")
        return False
    
    print(f"🛑 Stopping server (PID: {pid})...")
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        print("✅ Server stopped successfully")
        return True
    except psutil.TimeoutExpired:
        print("⚠️ Server didn't stop gracefully, forcing...")
        proc.kill()
        print("✅ Server killed")
        return True
    except Exception as e:
        print(f"❌ Error stopping server: {e}")
        return False

def restart_server():
    """Restart the server"""
    print("🔄 Restarting server...")
    stop_server()
    time.sleep(1)
    start_server()

def show_status():
    """Show server status"""
    running, pid = is_server_running()
    if running:
        print(f"✅ Server is RUNNING (PID: {pid})")
        print(f"🌐 Server URL: http://localhost:{SERVER_PORT}")
        try:
            proc = psutil.Process(pid)
            print(f"📊 Memory: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
            print(f"⏱️ CPU: {proc.cpu_percent(interval=0.5):.1f}%")
            print(f"🕐 Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))}")
        except Exception as e:
            print(f"⚠️ Couldn't get process details: {e}")
    else:
        print("❌ Server is NOT running")

def show_menu():
    """Show interactive menu"""
    while True:
        print("\n" + "="*50)
        print("🎛️  VONAGE AGENT SERVER MANAGER")
        print("="*50)
        show_status()
        print("\n" + "-"*50)
        print("1. Start Server")
        print("2. Stop Server")
        print("3. Restart Server")
        print("4. Refresh Status")
        print("5. Exit")
        print("-"*50)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            start_server()
        elif choice == '2':
            stop_server()
        elif choice == '3':
            restart_server()
        elif choice == '4':
            show_status()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil module not installed")
        print("Install it with: pip install psutil")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # If command line arguments provided, use them
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'start':
            start_server()
        elif command == 'stop':
            stop_server()
        elif command == 'restart':
            restart_server()
        elif command == 'status':
            show_status()
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python server_manager.py [start|stop|restart|status]")
    else:
        # Interactive menu
        show_menu()
