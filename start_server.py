"""
AI Phone Agent - Server Launcher
=================================
Automatically updates from Git and starts the server.

Usage: python start_server.py
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_header():
    """Print startup header"""
    print("\n" + "=" * 70)
    print("  AI PHONE AGENT - Server Launcher")
    print("=" * 70 + "\n")

def check_git_updates():
    """Check and pull latest updates from Git repository"""
    print("Checking for updates from Git...")
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode != 0:
            print("WARNING: Not a Git repository - skipping update check")
            return False
        
        # Fetch latest changes
        subprocess.run(
            ["git", "fetch"],
            capture_output=True,
            cwd=os.path.dirname(__file__)
        )
        
        # Check if we're behind
        result = subprocess.run(
            ["git", "status", "-uno"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if "Your branch is behind" in result.stdout:
            print("Updates available! Pulling latest changes...")
            pull_result = subprocess.run(
                ["git", "pull"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if pull_result.returncode == 0:
                print("Successfully updated from Git!")
                return True
            else:
                print(f"Failed to update: {pull_result.stderr}")
                return False
        else:
            print("Already up to date!")
            return False
            
    except FileNotFoundError:
        print("WARNING: Git not found - skipping update check")
        return False
    except Exception as e:
        print(f"WARNING: Error checking for updates: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    required = ["fastapi", "uvicorn", "websockets", "numpy", "scipy"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  OK: {package}")
        except ImportError:
            missing.append(package)
            print(f"  MISSING: {package}")
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print(f"Install them with: pip install {' '.join(missing)}")
        return False
    
    print("All dependencies installed!")
    return True

def start_server():
    """Start the Vonage agent server"""
    print("\nStarting AI Phone Agent server...")
    print("   Web Interface: http://localhost:5004")
    print("   Press Ctrl+C to stop the server\n")
    print("-" * 70 + "\n")
    
    try:
        # Run the server using subprocess
        subprocess.run(
            [sys.executable, "vonage_agent.py"],
            cwd=os.path.dirname(__file__) or "."
        )
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main launcher function"""
    print_header()
    
    # Check for Git updates
    updated = check_git_updates()
    
    if updated:
        print("\nWARNING: Files were updated. Please restart the script to use the latest version.")
        print("   Run: python start_server.py")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\nWARNING: Please install missing dependencies and try again.")
        return
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
