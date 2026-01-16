import psutil
import os
import sys
import threading
import time
import webbrowser
import socket
import requests
import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sqlite3
from datetime import datetime
import json

SERVER_SCRIPT = "vonage_agent.py"
SERVER_PORT = 5004

class ServerControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎛️ Vonage Server Control")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        # Set icon color
        self.root.configure(bg='#2c3e50')
        
        # Main container
        main_frame = tk.Frame(root, bg='#2c3e50', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            main_frame, 
            text="🚀 Vonage Agent Server Control",
            font=('Segoe UI', 16, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title.pack(pady=(0, 10))
        
        # Status Indicators Frame - Compact single row
        indicators_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2, padx=10, pady=8)
        indicators_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create horizontal row for all indicators
        indicators_row = tk.Frame(indicators_frame, bg='#34495e')
        indicators_row.pack()
        
        # All indicators in one row
        self.server_indicator = self.create_indicator(indicators_row, "Server", 0)
        self.ngrok_indicator = self.create_indicator(indicators_row, "Ngrok", 1)
        self.calls_indicator = self.create_indicator(indicators_row, "Calls", 2)
        self.network_indicator = self.create_indicator(indicators_row, "Network", 3)
        self.cpu_indicator = self.create_indicator(indicators_row, "CPU", 4)
        self.ram_indicator = self.create_indicator(indicators_row, "RAM", 5)
        
        # Status Frame
        status_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame,
            text="● Server Status: Checking...",
            font=('Segoe UI', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            pady=15
        )
        self.status_label.pack()
        
        # Info display
        info_frame = tk.Frame(status_frame, bg='#34495e')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.info_text = tk.Label(
            info_frame,
            text="",
            font=('Consolas', 9),
            bg='#34495e',
            fg='#bdc3c7',
            justify=tk.LEFT,
            anchor='w'
        )
        self.info_text.pack(fill=tk.X)
        
        # Buttons Frame
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=(0, 20))
        
        button_style = {
            'font': ('Segoe UI', 9, 'bold'),
            'width': 12,
            'height': 1,
            'relief': tk.RAISED,
            'bd': 2,
            'cursor': 'hand2'
        }
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶️ Start Server",
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            command=self.start_server,
            **button_style
        )
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ Stop Server",
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            command=self.stop_server,
            **button_style
        )
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.restart_btn = tk.Button(
            button_frame,
            text="🔄 Restart Server",
            bg='#f39c12',
            fg='white',
            activebackground='#d68910',
            command=self.restart_server,
            **button_style
        )
        self.restart_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.refresh_btn = tk.Button(
            button_frame,
            text="🔃 Refresh Status",
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            command=self.update_status,
            **button_style
        )
        self.refresh_btn.grid(row=1, column=1, padx=5, pady=5)
        
        self.web_btn = tk.Button(
            button_frame,
            text="🌐 Open Website",
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            command=self.open_website,
            **button_style
        )
        self.web_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        self.ngrok_start_btn = tk.Button(
            button_frame,
            text="🚀 Start Ngrok",
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            command=self.start_ngrok,
            font=('Segoe UI', 9, 'bold'),
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2'
        )
        self.ngrok_start_btn.grid(row=3, column=0, padx=5, pady=5, sticky='ew')
        
        self.ngrok_reset_btn = tk.Button(
            button_frame,
            text="🔄 Reset Ngrok",
            bg='#e67e22',
            fg='white',
            activebackground='#d35400',
            command=self.reset_ngrok,
            font=('Segoe UI', 9, 'bold'),
            width=12,
            height=1,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2'
        )
        self.ngrok_reset_btn.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        
        # Git buttons
        self.git_push_btn = tk.Button(
            button_frame,
            text="⬆️ Push to Git",
            bg='#16a085',
            fg='white',
            activebackground='#138d75',
            command=self.git_push,
            **button_style
        )
        self.git_push_btn.grid(row=4, column=0, padx=5, pady=5)
        
        self.git_pull_btn = tk.Button(
            button_frame,
            text="⬇️ Pull from Git",
            bg='#2980b9',
            fg='white',
            activebackground='#21618c',
            command=self.git_pull,
            **button_style
        )
        self.git_pull_btn.grid(row=4, column=1, padx=5, pady=5)
        
        # Manage Numbers button
        self.manage_numbers_btn = tk.Button(
            button_frame,
            text="📞 Manage Numbers",
            bg='#8e44ad',
            fg='white',
            activebackground='#7d3c98',
            command=self.show_numbers_popup,
            **button_style
        )
        self.manage_numbers_btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        # Manage Users button
        self.manage_users_btn = tk.Button(
            button_frame,
            text="👥 Manage Users",
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            command=self.show_manage_users,
            **button_style
        )
        self.manage_users_btn.grid(row=5, column=2, padx=5, pady=5, sticky='ew')
        
        # Billing Settings button
        self.billing_btn = tk.Button(
            button_frame,
            text="💰 Billing Settings",
            bg='#f39c12',
            fg='white',
            activebackground='#e67e22',
            command=self.show_billing_settings,
            **button_style
        )
        self.billing_btn.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        # Voice Diagnostics button
        self.voice_diagnostics_btn = tk.Button(
            button_frame,
            text="🔍 Voice Diagnostics",
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            command=self.show_voice_diagnostics,
            **button_style
        )
        self.voice_diagnostics_btn.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        # Live Call Diagnostics button
        self.live_diagnostics_btn = tk.Button(
            button_frame,
            text="📊 Live Call Diagnostics",
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            command=self.show_live_diagnostics,
            **button_style
        )
        self.live_diagnostics_btn.grid(row=7, column=2, padx=5, pady=5, sticky='ew')
        
        # Open Admin Dashboard button
        self.admin_dashboard_btn = tk.Button(
            button_frame,
            text="🌐 Open Admin Dashboard",
            bg='#e67e22',
            fg='white',
            activebackground='#d35400',
            command=self.open_admin_dashboard,
            **button_style
        )
        self.admin_dashboard_btn.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        # Log Frame
        log_label = tk.Label(
            main_frame,
            text="📋 Activity Log",
            font=('Segoe UI', 9, 'bold'),
            bg='#2c3e50',
            fg='white',
            anchor='w'
        )
        log_label.pack(fill=tk.X, pady=(0, 3))
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=10,
            font=('Consolas', 8),
            bg='#1a1a1a',
            fg='#00ff00',
            insertbackground='white',
            relief=tk.SUNKEN,
            bd=2
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Make log read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Start status updater
        self.update_status()
        self.update_indicators()
        self.root.after(3000, self.auto_refresh)
        self.root.after(2000, self.auto_update_indicators)
    
    def create_indicator(self, parent, label_text, col):
        """Create a compact status indicator with label"""
        container = tk.Frame(parent, bg='#34495e')
        container.grid(row=0, column=col, padx=5, pady=2)
        
        # Canvas for the small bulb
        canvas = tk.Canvas(container, width=20, height=20, bg='#34495e', highlightthickness=0)
        canvas.pack()
        
        # Draw small circle (bulb)
        circle = canvas.create_oval(3, 3, 17, 17, fill='#95a5a6', outline='#7f8c8d', width=1)
        
        # Make canvas clickable
        canvas.bind('<Button-1>', lambda e, name=label_text: self.show_indicator_info(name))
        canvas.config(cursor='hand2')
        
        # Label
        label = tk.Label(
            container,
            text=label_text,
            font=('Segoe UI', 7),
            bg='#34495e',
            fg='#ecf0f1'
        )
        label.pack()
        
        return {'canvas': canvas, 'circle': circle, 'label': label, 'flicker': False}
    
    def set_indicator_color(self, indicator, status):
        """Set indicator color with flicker effect: green (good), amber (ok), red (warning), gray (offline)"""
        colors = {
            'green': '#2ecc71',
            'amber': '#f39c12',
            'red': '#e74c3c',
            'gray': '#95a5a6'
        }
        base_color = colors.get(status, '#95a5a6')
        
        # Add flicker effect for active statuses
        if status != 'gray' and indicator.get('flicker'):
            # Slightly dimmed version for flicker
            flicker_colors = {
                'green': '#27ae60',
                'amber': '#e67e22',
                'red': '#c0392b'
            }
            base_color = flicker_colors.get(status, base_color)
        
        indicator['canvas'].itemconfig(indicator['circle'], fill=base_color)
        indicator['flicker'] = not indicator.get('flicker', False)
        
    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def get_pid_on_port(self, port):
        """Find process ID using the specified port"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections()
                for conn in connections:
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return proc.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        return None
    
    def is_server_running(self):
        """Check if server is running"""
        pid = self.get_pid_on_port(SERVER_PORT)
        return pid is not None, pid
    
    def update_status(self):
        """Update status display"""
        running, pid = self.is_server_running()
        
        if running:
            try:
                proc = psutil.Process(pid)
                mem_mb = proc.memory_info().rss / 1024 / 1024
                cpu = proc.cpu_percent(interval=0.1)
                uptime = time.time() - proc.create_time()
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                
                self.status_label.config(
                    text="● Server Status: RUNNING",
                    fg='#2ecc71'
                )
                
                info = f"PID: {pid} | Port: {SERVER_PORT} | Memory: {mem_mb:.1f} MB | CPU: {cpu:.1f}% | Uptime: {hours}h {minutes}m"
                self.info_text.config(text=info)
                
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.restart_btn.config(state=tk.NORMAL)
                
            except Exception as e:
                self.log(f"⚠️ Error getting process info: {e}")
        else:
            self.status_label.config(
                text="● Server Status: STOPPED",
                fg='#e74c3c'
            )
            self.info_text.config(text="Server is not running")
            
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
    
    def auto_refresh(self):
        """Auto-refresh status every 3 seconds"""
        self.update_status()
        self.root.after(3000, self.auto_refresh)
    
    def auto_update_indicators(self):
        """Auto-update indicators every 2 seconds with flicker effect"""
        self.update_indicators()
        self.root.after(1500, self.auto_update_indicators)  # Faster for flicker effect
    
    def update_indicators(self):
        """Update all status indicators"""
        try:
            # Server indicator
            running, pid = self.is_server_running()
            self.set_indicator_color(self.server_indicator, 'green' if running else 'gray')
            
            # Ngrok indicator
            ngrok_status = self.check_ngrok()
            if ngrok_status == 'running':
                self.set_indicator_color(self.ngrok_indicator, 'green')
            elif ngrok_status == 'error':
                self.set_indicator_color(self.ngrok_indicator, 'red')
            else:
                self.set_indicator_color(self.ngrok_indicator, 'gray')
            
            # Active calls indicator
            active_calls = self.check_active_calls()
            if active_calls > 0:
                self.set_indicator_color(self.calls_indicator, 'green')
            else:
                self.set_indicator_color(self.calls_indicator, 'gray')
            
            # Network indicator
            network_status = self.check_network()
            self.set_indicator_color(self.network_indicator, network_status)
            
            # CPU indicator
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent < 50:
                self.set_indicator_color(self.cpu_indicator, 'green')
            elif cpu_percent < 80:
                self.set_indicator_color(self.cpu_indicator, 'amber')
            else:
                self.set_indicator_color(self.cpu_indicator, 'red')
            
            # RAM indicator
            ram_percent = psutil.virtual_memory().percent
            if ram_percent < 70:
                self.set_indicator_color(self.ram_indicator, 'green')
            elif ram_percent < 85:
                self.set_indicator_color(self.ram_indicator, 'amber')
            else:
                self.set_indicator_color(self.ram_indicator, 'red')
                
        except Exception as e:
            pass  # Silently handle indicator update errors
    
    def check_ngrok(self):
        """Check if ngrok is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'ngrok' in proc.info['name'].lower():
                    return 'running'
            return 'offline'
        except:
            return 'offline'
    
    def check_active_calls(self):
        """Check number of active calls via API"""
        try:
            response = requests.get(f"http://localhost:{SERVER_PORT}/api/active-calls", timeout=1)
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                if count > 0:
                    self.log(f"Active calls: {count}")
                return count
            return 0
        except Exception as e:
            # API not available - server may need restart
            return 0
    
    def check_network(self):
        """Check network connectivity and speed"""
        try:
            # Quick ping to Google DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            
            if result == 0:
                return 'green'  # Connected
            else:
                return 'red'  # No connection
        except:
            return 'red'
    
    def reset_ngrok(self):
        """Reset ngrok by killing and restarting it"""
        def _reset():
            try:
                self.log("🔄 Resetting ngrok...")
                
                # Kill all ngrok processes
                killed = False
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'ngrok' in proc.info['name'].lower():
                        try:
                            proc.kill()
                            killed = True
                            self.log(f"✅ Killed ngrok process (PID: {proc.info['pid']})")
                        except Exception as kill_error:
                            self.log(f"⚠️ Error killing process: {kill_error}")
                
                if killed:
                    self.log("⏳ Waiting for ngrok to fully stop...")
                    time.sleep(2)
                else:
                    self.log("⚠️ No ngrok process found running - will start fresh")
                
                # Start ngrok
                self.log("🚀 Starting ngrok on port 5004...")
                ngrok_path = r"C:\ngrok\ngrok.exe"
                
                if not os.path.exists(ngrok_path):
                    self.log(f"❌ ngrok.exe not found at {ngrok_path}")
                    self.log("💡 Please install ngrok or update the path in the script")
                    return
                
                try:
                    # Use os.startfile to launch ngrok in a new window
                    # This is more reliable than subprocess.Popen on Windows
                    import subprocess
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    proc = subprocess.Popen(
                        f'"{ngrok_path}" http 5004',
                        shell=True,
                        startupinfo=startupinfo
                    )
                    
                    self.log(f"✅ Ngrok started successfully! (PID: {proc.pid})")
                    self.log("💡 Visit http://localhost:4040 to see your ngrok URL")
                    
                    # Give it a moment to start
                    time.sleep(2)
                    self.update_indicators()
                    
                except Exception as start_error:
                    self.log(f"❌ Failed to start ngrok: {start_error}")
                    import traceback
                    self.log(traceback.format_exc())
                    
            except Exception as e:
                self.log(f"❌ Error resetting ngrok: {e}")
                import traceback
                self.log(traceback.format_exc())
        
        threading.Thread(target=_reset, daemon=True).start()
    
    def start_ngrok(self):
        """Start ngrok without killing existing processes"""
        def _start():
            try:
                # Check if ngrok is already running
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'ngrok' in proc.info['name'].lower():
                        self.log(f"⚠️ Ngrok is already running (PID: {proc.info['pid']})")
                        self.log("💡 Use Reset Ngrok to restart it")
                        return
                
                self.log("🚀 Starting ngrok on port 5004...")
                ngrok_path = r"C:\ngrok\ngrok.exe"
                
                if not os.path.exists(ngrok_path):
                    self.log(f"❌ ngrok.exe not found at {ngrok_path}")
                    self.log("💡 Please install ngrok or update the path in the script")
                    return
                
                try:
                    # Use shell=True for better compatibility
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    proc = subprocess.Popen(
                        f'"{ngrok_path}" http 5004',
                        shell=True,
                        startupinfo=startupinfo
                    )
                    
                    self.log(f"✅ Ngrok started successfully! (PID: {proc.pid})")
                    self.log("💡 Visit http://localhost:4040 to see your ngrok URL")
                    
                    # Give it a moment to start
                    time.sleep(2)
                    self.update_indicators()
                    
                except Exception as start_error:
                    self.log(f"❌ Failed to start ngrok: {start_error}")
                    import traceback
                    self.log(traceback.format_exc())
                    
            except Exception as e:
                self.log(f"❌ Error starting ngrok: {e}")
                import traceback
                self.log(traceback.format_exc())
        
        threading.Thread(target=_start, daemon=True).start()
    
    def start_server(self):
        """Start the server"""
        def _start():
            running, pid = self.is_server_running()
            if running:
                self.log(f"❌ Server already running (PID: {pid})")
                return
            
            self.log("🚀 Starting server...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, SERVER_SCRIPT)
            log_path = os.path.join(script_dir, "server_startup.log")
            
            try:
                # Prefer the workspace virtualenv interpreter (python.exe) to avoid
                # accidentally spawning pythonw.exe child processes that can silently
                # hold the port and cause confusing restart/terminal flashing.
                venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
                python_exe = venv_python if os.path.exists(venv_python) else sys.executable

                # Open log file for output
                with open(log_path, 'w') as log_file:
                    proc = subprocess.Popen(
                        [python_exe, script_path],
                        cwd=script_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL
                    )
                
                # Wait longer and check multiple times
                time.sleep(5)
                running, pid = self.is_server_running()
                if running:
                    self.log(f"✅ Server started successfully (PID: {pid})")
                    self.log(f"🌐 URL: http://localhost:{SERVER_PORT}")
                else:
                    # Check if process is still alive
                    try:
                        proc_status = proc.poll()
                        if proc_status is not None:
                            self.log(f"❌ Server process exited with code: {proc_status}")
                    except:
                        pass
                    
                    self.log("❌ Failed to start server")
                    # Show detailed error from log file
                    time.sleep(1)  # Extra wait for log to be written
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                            if log_content.strip():
                                self.log("📋 Full server output:")
                                lines = log_content.split('\n')
                                # Skip ffmpeg warning, show everything else
                                for line in lines:
                                    if line.strip() and 'ffmpeg' not in line.lower():
                                        self.log(f"   {line}")
                                # If only ffmpeg warning, show it anyway
                                if all('ffmpeg' in line.lower() or not line.strip() for line in lines):
                                    self.log("   [Only ffmpeg warning - server may have crashed]")
                                    for line in lines:
                                        if line.strip():
                                            self.log(f"   {line}")
                            else:
                                self.log("💡 No error output - check if vonage_agent.py exists")
                    except Exception as read_err:
                        self.log(f"⚠️ Could not read log file: {read_err}")
            except Exception as e:
                self.log(f"❌ Error starting server: {e}")
                import traceback
                self.log(f"📋 Traceback: {traceback.format_exc()}")
            
            self.update_status()
        
        threading.Thread(target=_start, daemon=True).start()
    
    def stop_server(self):
        """Stop the server"""
        def _stop():
            running, pid = self.is_server_running()
            if not running:
                self.log("❌ Server is not running")
                return
            
            self.log(f"🛑 Stopping server (PID: {pid})...")
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
                self.log("✅ Server stopped successfully")
            except psutil.TimeoutExpired:
                self.log("⚠️ Forcing shutdown...")
                proc.kill()
                self.log("✅ Server killed")
            except Exception as e:
                self.log(f"❌ Error stopping server: {e}")
            
            time.sleep(1)
            self.update_status()
        
        threading.Thread(target=_stop, daemon=True).start()
    
    def restart_server(self):
        """Restart the server"""
        def _restart():
            self.log("🔄 Restarting server...")
            
            # Stop
            running, pid = self.is_server_running()
            if running:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                    self.log("✅ Server stopped")
                except Exception as e:
                    self.log(f"⚠️ Error during stop: {e}")
            
            time.sleep(1)
            
            # Start
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, SERVER_SCRIPT)
            
            try:
                venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
                python_exe = venv_python if os.path.exists(venv_python) else sys.executable

                subprocess.Popen(
                    [python_exe, script_path],
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
                
                time.sleep(3)
                running, pid = self.is_server_running()
                if running:
                    self.log(f"✅ Server restarted successfully (PID: {pid})")
                else:
                    self.log("❌ Failed to restart server")
            except Exception as e:
                self.log(f"❌ Error restarting server: {e}")
            
            self.update_status()
        
        threading.Thread(target=_restart, daemon=True).start()
    
    def open_website(self):
        """Open the website in default browser"""
        url = f"http://localhost:{SERVER_PORT}"
        try:
            webbrowser.open(url)
            self.log(f"🌐 Opening {url} in browser...")
        except Exception as e:
            self.log(f"❌ Error opening browser: {e}")
    
    def git_push(self):
        """Push changes to GitHub repository"""
        self.log("⬆️ Pushing changes to Git...")
        try:
            # Add all changes
            result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Commit changes
            result = subprocess.run(['git', 'commit', '-m', 'Auto-commit from GUI'], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            if 'nothing to commit' in result.stdout:
                self.log("✅ No changes to push")
                return
            
            # Push to remote
            result = subprocess.run(['git', 'push'], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                self.log("✅ Successfully pushed to Git")
            else:
                self.log(f"❌ Git push failed: {result.stderr}")
        except Exception as e:
            self.log(f"❌ Error pushing to Git: {e}")
    
    def git_pull(self):
        """Pull updates from GitHub repository"""
        self.log("⬇️ Pulling updates from Git...")
        try:
            result = subprocess.run(['git', 'pull'], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                if 'Already up to date' in result.stdout:
                    self.log("✅ Already up to date")
                else:
                    self.log("✅ Successfully pulled updates from Git")
                    self.log("🔄 Please restart server to apply changes")
            else:
                self.log(f"❌ Git pull failed: {result.stderr}")
        except Exception as e:
            self.log(f"❌ Error pulling from Git: {e}")
    
    def open_admin_dashboard(self):
        """Open the admin dashboard in the default web browser"""
        try:
            url = f"http://localhost:{SERVER_PORT}/static/admin.html"
            self.log(f"🌐 Opening admin dashboard at {url}")
            webbrowser.open(url)
        except Exception as e:
            self.log(f"❌ Failed to open admin dashboard: {e}")
    
    def show_manage_users(self):
        """Show user management popup with delete functionality"""
        self.log("👥 Loading users...")
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("User Management")
        popup.geometry("800x600")
        popup.resizable(True, True)
        popup.configure(bg='#34495e')
        
        # Center popup on parent
        popup.transient(self.root)
        
        # Title
        title_label = tk.Label(
            popup,
            text="👥 User Management",
            font=('Segoe UI', 14, 'bold'),
            bg='#34495e',
            fg='white'
        )
        title_label.pack(pady=(15, 10))
        
        # Loading label
        loading_label = tk.Label(
            popup,
            text="Loading users...",
            font=('Segoe UI', 10),
            bg='#34495e',
            fg='#ecf0f1'
        )
        loading_label.pack(pady=20)
        
        # Fetch data in background
        def fetch_users():
            try:
                conn = sqlite3.connect('call_logs.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.id, u.name, u.email, a.phone_number, a.minutes_remaining
                    FROM users u
                    LEFT JOIN account_settings a ON u.id = a.user_id
                    ORDER BY u.name
                ''')
                users = cursor.fetchall()
                conn.close()
                
                popup.after(0, lambda: display_users(users))
            except Exception as e:
                popup.after(0, lambda: show_error(str(e)))
        
        def display_users(users):
            try:
                loading_label.destroy()
            except:
                pass
            
            if len(users) == 0:
                no_users_label = tk.Label(
                    popup,
                    text="❌ No users found.",
                    font=('Segoe UI', 10),
                    bg='#34495e',
                    fg='#e74c3c',
                    justify=tk.CENTER
                )
                no_users_label.pack(pady=30)
            else:
                # Create scrollable frame
                canvas = tk.Canvas(popup, bg='#34495e', highlightthickness=0)
                scrollbar = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg='#34495e')
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                # Summary
                summary = tk.Label(
                    scrollable_frame,
                    text=f"Total Users: {len(users)}",
                    font=('Segoe UI', 9, 'bold'),
                    bg='#2c3e50',
                    fg='white',
                    pady=8
                )
                summary.pack(fill=tk.X, padx=15, pady=(10, 15))
                
                for user in users:
                    user_id, name, email, phone_number, minutes_remaining = user
                    
                    user_frame = tk.Frame(scrollable_frame, bg='#2c3e50', relief=tk.RAISED, bd=1)
                    user_frame.pack(fill=tk.X, padx=15, pady=5)
                    
                    # User info
                    info_frame = tk.Frame(user_frame, bg='#2c3e50')
                    info_frame.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.X, expand=True)
                    
                    name_label = tk.Label(
                        info_frame,
                        text=f"👤 {name}",
                        font=('Segoe UI', 10, 'bold'),
                        bg='#2c3e50',
                        fg='#3498db',
                        anchor='w'
                    )
                    name_label.pack(anchor='w')
                    
                    email_label = tk.Label(
                        info_frame,
                        text=f"📧 {email}",
                        font=('Segoe UI', 9),
                        bg='#2c3e50',
                        fg='#ecf0f1',
                        anchor='w'
                    )
                    email_label.pack(anchor='w')
                    
                    if phone_number:
                        phone_label = tk.Label(
                            info_frame,
                            text=f"📞 {phone_number}",
                            font=('Segoe UI', 9),
                            bg='#2c3e50',
                            fg='#27ae60',
                            anchor='w'
                        )
                        phone_label.pack(anchor='w')
                    
                    minutes_label = tk.Label(
                        info_frame,
                        text=f"⏱️ {minutes_remaining or 0} minutes remaining",
                        font=('Segoe UI', 9),
                        bg='#2c3e50',
                        fg='#bdc3c7',
                        anchor='w'
                    )
                    minutes_label.pack(anchor='w')
                    
                    # Delete button
                    delete_btn = tk.Button(
                        user_frame,
                        text="🗑️ Delete User",
                        command=lambda u=user: delete_user(u, popup),
                        bg='#e74c3c',
                        fg='white',
                        font=('Segoe UI', 9, 'bold'),
                        cursor='hand2',
                        relief=tk.RAISED,
                        bd=1,
                        padx=15,
                        pady=5
                    )
                    delete_btn.pack(side=tk.RIGHT, padx=10, pady=8)
                
                canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Close button
            close_btn = tk.Button(
                popup,
                text="Close",
                command=popup.destroy,
                bg='#3498db',
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                cursor='hand2',
                relief=tk.RAISED,
                bd=2,
                padx=20,
                pady=5
            )
            close_btn.pack(pady=(0, 15))
        
        def show_error(error_msg):
            try:
                loading_label.destroy()
            except:
                pass
            error_label = tk.Label(
                popup,
                text=f"❌ {error_msg}",
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#e74c3c',
                wraplength=600
            )
            error_label.pack(pady=20)
        
        def delete_user(user, window):
            """Delete user and release their phone number"""
            import tkinter.messagebox as messagebox
            user_id, name, email, phone_number, minutes_remaining = user
            
            # Confirm deletion
            confirm_msg = f"Are you sure you want to delete user '{name}'?\n\n"
            if phone_number:
                confirm_msg += f"Phone number {phone_number} will be released and made available.\n\n"
            confirm_msg += "This action cannot be undone!"
            
            if not messagebox.askyesno("Confirm Deletion", confirm_msg):
                return
            
            try:
                self.log(f"🗑️ Deleting user {name} (ID: {user_id})...")
                
                conn = sqlite3.connect('call_logs.db')
                cursor = conn.cursor()
                
                # Release phone number if assigned
                if phone_number:
                    # Create table if doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS number_availability (
                            phone_number TEXT PRIMARY KEY,
                            is_available INTEGER DEFAULT 1,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Mark number as available
                    cursor.execute('''
                        INSERT INTO number_availability (phone_number, is_available, updated_at)
                        VALUES (?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(phone_number) DO UPDATE SET
                            is_available = 1,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (phone_number,))
                    
                    self.log(f"✅ Released phone number: {phone_number}")
                
                # Delete user data
                cursor.execute('DELETE FROM calls WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM appointments WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM account_settings WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                
                self.log(f"✅ User {name} deleted successfully")
                messagebox.showinfo("Success", f"User '{name}' has been deleted.")
                
                # Refresh the popup
                window.destroy()
                self.show_manage_users()
                
            except Exception as e:
                self.log(f"❌ Error deleting user: {e}")
                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
        
        # Start fetching in background thread
        import threading
        thread = threading.Thread(target=fetch_users, daemon=True)
        thread.start()
    
    def show_numbers_popup(self):
        """Show popup with owned Vonage numbers and their assignments"""
        self.log("📞 Loading number assignments...")
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Vonage Number Management")
        popup.geometry("700x500")
        popup.resizable(True, True)
        popup.configure(bg='#34495e')
        
        # Center popup on parent
        popup.transient(self.root)
        
        # Title
        title_label = tk.Label(
            popup,
            text="📞 Vonage Number Assignments",
            font=('Segoe UI', 14, 'bold'),
            bg='#34495e',
            fg='white'
        )
        title_label.pack(pady=(15, 5))
        
        # Sync button at top
        def sync_numbers():
            sync_btn.config(state='disabled', text='⏳ Syncing...')
            def do_sync():
                try:
                    response = requests.post(f"http://localhost:{SERVER_PORT}/api/sync-vonage-numbers", timeout=15)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            messagebox.showinfo("Sync Complete", result.get('message', 'Numbers synced!'))
                            popup.destroy()
                            self.show_numbers_popup()  # Reload
                        else:
                            messagebox.showerror("Sync Failed", result.get('error', 'Unknown error'))
                    else:
                        messagebox.showerror("Sync Failed", f"HTTP {response.status_code}")
                except Exception as e:
                    messagebox.showerror("Sync Error", str(e))
                finally:
                    try:
                        sync_btn.config(state='normal', text='🔄 Sync from Vonage')
                    except:
                        pass
            threading.Thread(target=do_sync, daemon=True).start()
        
        sync_btn = tk.Button(
            popup,
            text="🔄 Sync from Vonage",
            command=sync_numbers,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            padx=15,
            pady=5
        )
        sync_btn.pack(pady=(5, 10))
        
        # Loading label
        loading_label = tk.Label(
            popup,
            text="Loading numbers from database...",
            font=('Segoe UI', 10),
            bg='#34495e',
            fg='#ecf0f1'
        )
        loading_label.pack(pady=20)
        
        # Fetch data in background
        def fetch_numbers():
            try:
                response = requests.get(f"http://localhost:{SERVER_PORT}/api/owned-numbers", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    popup.after(0, lambda: display_numbers(data))
                else:
                    popup.after(0, lambda: show_error("Failed to fetch numbers from server"))
            except Exception as e:
                popup.after(0, lambda: show_error(f"Error: {str(e)}"))
        
        def display_numbers(data):
            try:
                loading_label.destroy()
            except:
                pass
            
            if not data.get('success'):
                show_error(data.get('error', 'Unknown error'))
                return
            
            numbers = data.get('numbers', [])
            
            if len(numbers) == 0:
                no_numbers_label = tk.Label(
                    popup,
                    text="❌ No Vonage numbers found.\n\nPurchase numbers from the Admin Dashboard.",
                    font=('Segoe UI', 10),
                    bg='#34495e',
                    fg='#e74c3c',
                    justify=tk.CENTER
                )
                no_numbers_label.pack(pady=30)
            else:
                # Create scrollable frame
                canvas = tk.Canvas(popup, bg='#34495e', highlightthickness=0)
                scrollbar = tk.Scrollbar(popup, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg='#34495e')
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                # Display numbers
                available_count = sum(1 for n in numbers if n.get('available'))
                
                summary = tk.Label(
                    scrollable_frame,
                    text=f"Total Numbers: {len(numbers)}  |  Available: {available_count}  |  Assigned: {len(numbers) - available_count}",
                    font=('Segoe UI', 9, 'bold'),
                    bg='#2c3e50',
                    fg='white',
                    pady=8
                )
                summary.pack(fill=tk.X, padx=15, pady=(10, 15))
                
                for number in numbers:
                    number_frame = tk.Frame(scrollable_frame, bg='#2c3e50', relief=tk.RAISED, bd=1)
                    number_frame.pack(fill=tk.X, padx=15, pady=5)
                    
                    # Number display
                    number_text = f"📞 {number.get('number')} ({number.get('country')})" if number.get('country') else f"📞 {number.get('number')}"
                    number_label = tk.Label(
                        number_frame,
                        text=number_text,
                        font=('Segoe UI', 10, 'bold'),
                        bg='#2c3e50',
                        fg='#3498db',
                        anchor='w'
                    )
                    number_label.pack(side=tk.LEFT, padx=10, pady=8)
                    
                    # Button container
                    button_frame = tk.Frame(number_frame, bg='#2c3e50')
                    button_frame.pack(side=tk.RIGHT, padx=10, pady=5)
                    
                    # Assignment status
                    if number.get('available'):
                        status_label = tk.Label(
                            button_frame,
                            text="✅ AVAILABLE",
                            font=('Segoe UI', 9, 'bold'),
                            bg='#27ae60',
                            fg='white',
                            padx=10,
                            pady=3
                        )
                        status_label.pack(side=tk.LEFT, padx=(0, 10))
                        
                        # Make unavailable button
                        toggle_btn = tk.Button(
                            button_frame,
                            text="🔒 Make Unavailable",
                            command=lambda n=number: toggle_availability(n, popup),
                            bg='#e74c3c',
                            fg='white',
                            font=('Segoe UI', 8, 'bold'),
                            cursor='hand2',
                            relief=tk.RAISED,
                            bd=1,
                            padx=8,
                            pady=3
                        )
                        toggle_btn.pack(side=tk.LEFT)
                    else:
                        assigned_text = f"Assigned to: {number.get('assigned_to')}"
                        status_label = tk.Label(
                            button_frame,
                            text=assigned_text,
                            font=('Segoe UI', 9),
                            bg='#2c3e50',
                            fg='#ecf0f1',
                            anchor='w'
                        )
                        status_label.pack(side=tk.LEFT, padx=(0, 10))
                        
                        # If assigned to a user, add deassign button
                        if number.get('assigned_to') and number.get('user_id'):
                            deassign_btn = tk.Button(
                                button_frame,
                                text="❌ Deassign",
                                command=lambda n=number: deassign_number(n, popup),
                                bg='#e67e22',
                                fg='white',
                                font=('Segoe UI', 8, 'bold'),
                                cursor='hand2',
                                relief=tk.RAISED,
                                bd=1,
                                padx=8,
                                pady=3
                            )
                            deassign_btn.pack(side=tk.LEFT)
                        else:
                            # If not assigned to user (manually unavailable), allow making available
                            toggle_btn = tk.Button(
                                button_frame,
                                text="🔓 Make Available",
                                command=lambda n=number: toggle_availability(n, popup),
                                bg='#27ae60',
                                fg='white',
                                font=('Segoe UI', 8, 'bold'),
                                cursor='hand2',
                                relief=tk.RAISED,
                                bd=1,
                                padx=8,
                                pady=3
                            )
                            toggle_btn.pack(side=tk.LEFT)
                
                canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Close button
            close_btn = tk.Button(
                popup,
                text="Close",
                command=popup.destroy,
                bg='#3498db',
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                cursor='hand2',
                relief=tk.RAISED,
                bd=2,
                padx=20,
                pady=5
            )
            close_btn.pack(pady=(0, 15))
        
        def show_error(error_msg):
            try:
                loading_label.destroy()
            except:
                pass
            error_label = tk.Label(
                popup,
                text=f"❌ {error_msg}",
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#e74c3c',
                wraplength=600
            )
            error_label.pack(pady=20)
        
        def toggle_availability(number, window):
            """Toggle availability status of a number"""
            try:
                phone_number = number.get('number')
                current_status = number.get('available', False)
                new_status = not current_status
                
                self.log(f"🔄 Toggling {phone_number} to {'available' if new_status else 'unavailable'}...")
                
                # Update in database
                import sqlite3
                script_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(script_dir, "call_logs.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Create availability tracking table if doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS number_availability (
                        phone_number TEXT PRIMARY KEY,
                        is_available INTEGER DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert or update availability
                cursor.execute('''
                    INSERT INTO number_availability (phone_number, is_available, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(phone_number) DO UPDATE SET
                        is_available = excluded.is_available,
                        updated_at = excluded.updated_at
                ''', (phone_number, 1 if new_status else 0))
                
                conn.commit()
                conn.close()
                
                status_text = "available" if new_status else "unavailable"
                self.log(f"✅ {phone_number} is now {status_text}")
                
                # Refresh the popup
                window.destroy()
                self.show_numbers_popup()
                
            except Exception as e:
                self.log(f"❌ Error toggling number availability: {e}")
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", f"Failed to toggle number: {str(e)}")
        
        def deassign_number(number, window):
            """Deassign a number from a user and make it available"""
            try:
                phone_number = number.get('number')
                user_name = number.get('assigned_to')
                
                # Confirm deassignment
                import tkinter.messagebox as messagebox
                confirm = messagebox.askyesno(
                    "Confirm Deassignment",
                    f"Are you sure you want to deassign {phone_number} from {user_name}?\n\nThis will remove the number from their account and make it available for reassignment."
                )
                
                if not confirm:
                    return
                
                self.log(f"🔄 Deassigning {phone_number} from {user_name}...")
                
                # Update in database
                import sqlite3
                script_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(script_dir, "call_logs.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Remove from account_settings
                cursor.execute('''
                    UPDATE account_settings 
                    SET phone_number = NULL 
                    WHERE phone_number = ?
                ''', (phone_number,))
                
                # Make it available in availability table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS number_availability (
                        phone_number TEXT PRIMARY KEY,
                        is_available INTEGER DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    INSERT INTO number_availability (phone_number, is_available, updated_at)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(phone_number) DO UPDATE SET
                        is_available = 1,
                        updated_at = CURRENT_TIMESTAMP
                ''', (phone_number,))
                
                conn.commit()
                conn.close()
                
                self.log(f"✅ {phone_number} deassigned from {user_name} and is now available")
                
                # Refresh the popup
                window.destroy()
                self.show_numbers_popup()
                
            except Exception as e:
                self.log(f"❌ Error deassigning number: {e}")
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", f"Failed to deassign number: {str(e)}")
        
        # Start fetching in background thread
        import threading
        thread = threading.Thread(target=fetch_numbers, daemon=True)
        thread.start()
    
    def show_indicator_info(self, indicator_name):
        """Show popup with indicator information"""
        info_data = {
            'Server': {
                'title': 'Server Status',
                'description': 'Shows if the Vonage Agent server is running on port 5004.',
                'colors': {
                    'Green': 'Server is running normally',
                    'Gray': 'Server is stopped'
                }
            },
            'Ngrok': {
                'title': 'Ngrok Status',
                'description': 'Shows if ngrok tunnel is active for exposing local server to internet.',
                'colors': {
                    'Green': 'Ngrok tunnel is running',
                    'Gray': 'Ngrok is not running',
                    'Red': 'Ngrok encountered an error'
                }
            },
            'Calls': {
                'title': 'Active Calls',
                'description': 'Shows if there are active phone calls connected to the server.',
                'colors': {
                    'Green': 'Active calls in progress',
                    'Gray': 'No active calls'
                }
            },
            'Network': {
                'title': 'Network Status',
                'description': 'Shows internet connectivity status.',
                'colors': {
                    'Green': 'Internet connection is working',
                    'Red': 'No internet connection detected'
                }
            },
            'CPU': {
                'title': 'CPU Usage',
                'description': 'Shows system CPU usage level.',
                'colors': {
                    'Green': 'CPU usage below 50% (optimal)',
                    'Amber': 'CPU usage 50-80% (moderate)',
                    'Red': 'CPU usage above 80% (high load)'
                }
            },
            'RAM': {
                'title': 'Memory Usage',
                'description': 'Shows system RAM (memory) usage level.',
                'colors': {
                    'Green': 'RAM usage below 70% (healthy)',
                    'Amber': 'RAM usage 70-85% (getting full)',
                    'Red': 'RAM usage above 85% (critical)'
                }
            }
        }
        
        info = info_data.get(indicator_name, {})
        if not info:
            return
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(info['title'])
        popup.geometry("350x250")
        popup.resizable(False, False)
        popup.configure(bg='#34495e')
        
        # Center popup on parent
        popup.transient(self.root)
        popup.grab_set()
        
        # Title
        title_label = tk.Label(
            popup,
            text=info['title'],
            font=('Segoe UI', 14, 'bold'),
            bg='#34495e',
            fg='white'
        )
        title_label.pack(pady=(15, 10))
        
        # Description
        desc_label = tk.Label(
            popup,
            text=info['description'],
            font=('Segoe UI', 10),
            bg='#34495e',
            fg='#ecf0f1',
            wraplength=300,
            justify=tk.LEFT
        )
        desc_label.pack(pady=(0, 15), padx=20)
        
        # Color meanings frame
        colors_frame = tk.Frame(popup, bg='#2c3e50', padx=15, pady=10)
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        color_label = tk.Label(
            colors_frame,
            text="Status Colors:",
            font=('Segoe UI', 10, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        color_label.pack(anchor='w', pady=(0, 8))
        
        for color, meaning in info['colors'].items():
            color_row = tk.Frame(colors_frame, bg='#2c3e50')
            color_row.pack(anchor='w', pady=2)
            
            # Color indicator
            color_map = {'Green': '#2ecc71', 'Amber': '#f39c12', 'Red': '#e74c3c', 'Gray': '#95a5a6'}
            canvas = tk.Canvas(color_row, width=12, height=12, bg='#2c3e50', highlightthickness=0)
            canvas.pack(side=tk.LEFT, padx=(0, 8))
            canvas.create_oval(1, 1, 11, 11, fill=color_map.get(color, '#95a5a6'), outline='')
            
            # Meaning text
            meaning_label = tk.Label(
                color_row,
                text=f"{color}: {meaning}",
                font=('Segoe UI', 9),
                bg='#2c3e50',
                fg='#ecf0f1',
                anchor='w'
            )
            meaning_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Button(
            popup,
            text="Close",
            command=popup.destroy,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=5
        )
        close_btn.pack(pady=(0, 15))
    
    def show_billing_settings(self):
        """Show billing configuration window"""
        popup = tk.Toplevel(self.root)
        popup.title("💰 Billing Settings")
        popup.geometry("600x650")
        popup.configure(bg='#2c3e50')
        popup.resizable(False, False)
        
        # Center window
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (650 // 2)
        popup.geometry(f'600x650+{x}+{y}')
        
        # Title
        title_label = tk.Label(
            popup,
            text="💰 Credit Billing Configuration",
            font=('Segoe UI', 16, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(
            popup,
            text="Set credit costs for various services. Users will be charged these amounts.",
            font=('Segoe UI', 9),
            bg='#2c3e50',
            fg='#bdc3c7',
            wraplength=550
        )
        desc_label.pack(pady=(0, 20))
        
        # Settings frame
        settings_frame = tk.Frame(popup, bg='#34495e', relief=tk.RAISED, bd=2)
        settings_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Load current settings from database
        try:
            import sqlite3
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "call_logs.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create billing_config table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS billing_config (
                    id INTEGER PRIMARY KEY,
                    credits_per_connected_call REAL DEFAULT 5.0,
                    credits_per_minute REAL DEFAULT 2.0,
                    credits_per_calendar_booking REAL DEFAULT 10.0,
                    credits_per_task REAL DEFAULT 5.0,
                    credits_per_advanced_voice REAL DEFAULT 3.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add missing columns if they don't exist
            try:
                cursor.execute('ALTER TABLE billing_config ADD COLUMN credits_per_task REAL DEFAULT 5.0')
            except:
                pass
            
            try:
                cursor.execute('ALTER TABLE billing_config ADD COLUMN credits_per_advanced_voice REAL DEFAULT 3.0')
            except:
                pass
            
            try:
                cursor.execute('ALTER TABLE billing_config ADD COLUMN credits_per_sales_detection REAL DEFAULT 2.0')
            except:
                pass
            
            # Get current values or insert defaults
            cursor.execute('SELECT credits_per_connected_call, credits_per_minute, credits_per_calendar_booking, credits_per_task, credits_per_advanced_voice, credits_per_sales_detection FROM billing_config WHERE id = 1')
            config = cursor.fetchone()
            if not config:
                cursor.execute('''
                    INSERT INTO billing_config (id, credits_per_connected_call, credits_per_minute, credits_per_calendar_booking, credits_per_task, credits_per_advanced_voice, credits_per_sales_detection)
                    VALUES (1, 5.0, 2.0, 10.0, 5.0, 3.0, 2.0)
                ''')
                conn.commit()
                config = (5.0, 2.0, 10.0, 5.0, 3.0, 2.0)
            
            conn.close()
            
            current_call_credits = config[0]
            current_minute_credits = config[1]
            current_booking_credits = config[2]
            current_task_credits = config[3] if len(config) > 3 else 5.0
            current_advanced_voice_credits = config[4] if len(config) > 4 else 3.0
            current_sales_detector_credits = config[5] if len(config) > 5 else 2.0
        except Exception as e:
            self.log(f"⚠️ Error loading billing config: {e}")
            current_call_credits = 5.0
            current_minute_credits = 2.0
            current_booking_credits = 10.0
            current_task_credits = 5.0
            current_sales_detector_credits = 2.0
            current_advanced_voice_credits = 3.0
        
        # Settings fields
        fields = []
        
        # Connected Call Credits
        call_frame = tk.Frame(settings_frame, bg='#34495e')
        call_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            call_frame,
            text="📞 Credits per Connected Call:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        call_entry = tk.Entry(call_frame, font=('Segoe UI', 10), width=10)
        call_entry.insert(0, str(current_call_credits))
        call_entry.pack(side=tk.LEFT)
        fields.append(('call', call_entry))
        
        tk.Label(
            call_frame,
            text="(charged when call connects)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Per Minute Credits
        minute_frame = tk.Frame(settings_frame, bg='#34495e')
        minute_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            minute_frame,
            text="⏱️ Credits per Minute of Call:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        minute_entry = tk.Entry(minute_frame, font=('Segoe UI', 10), width=10)
        minute_entry.insert(0, str(current_minute_credits))
        minute_entry.pack(side=tk.LEFT)
        fields.append(('minute', minute_entry))
        
        tk.Label(
            minute_frame,
            text="(per minute of conversation)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Calendar Booking Credits
        booking_frame = tk.Frame(settings_frame, bg='#34495e')
        booking_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            booking_frame,
            text="📅 Credits per Calendar Booking:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        booking_entry = tk.Entry(booking_frame, font=('Segoe UI', 10), width=10)
        booking_entry.insert(0, str(current_booking_credits))
        booking_entry.pack(side=tk.LEFT)
        fields.append(('booking', booking_entry))
        
        tk.Label(
            booking_frame,
            text="(when AI books appointment)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Task Extraction Credits
        task_frame = tk.Frame(settings_frame, bg='#34495e')
        task_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            task_frame,
            text="✓ Credits per Task Extraction:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        task_entry = tk.Entry(task_frame, font=('Segoe UI', 10), width=10)
        task_entry.insert(0, str(current_task_credits))
        task_entry.pack(side=tk.LEFT)
        fields.append(('task', task_entry))
        
        tk.Label(
            task_frame,
            text="(when AI extracts task from call)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Advanced Voice Credits
        voice_frame = tk.Frame(settings_frame, bg='#34495e')
        voice_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            voice_frame,
            text="🎙️ Credits per Advanced Voice Call:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        voice_entry = tk.Entry(voice_frame, font=('Segoe UI', 10), width=10)
        voice_entry.insert(0, str(current_advanced_voice_credits))
        voice_entry.pack(side=tk.LEFT)
        fields.append(('voice', voice_entry))
        
        tk.Label(
            voice_frame,
            text="(when advanced voice is used)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Sales Detector Credits
        sales_frame = tk.Frame(settings_frame, bg='#34495e')
        sales_frame.pack(padx=20, pady=15, fill=tk.X)
        
        tk.Label(
            sales_frame,
            text="🚫 Credits per Sales Call Detection:",
            font=('Segoe UI', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1',
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        sales_entry = tk.Entry(sales_frame, font=('Segoe UI', 10), width=10)
        sales_entry.insert(0, str(current_sales_detector_credits))
        sales_entry.pack(side=tk.LEFT)
        fields.append(('sales', sales_entry))
        
        tk.Label(
            sales_frame,
            text="(AI analyzes if call is a sales pitch)",
            font=('Segoe UI', 8),
            bg='#34495e',
            fg='#95a5a6'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Info box
        info_frame = tk.Frame(settings_frame, bg='#2c3e50', relief=tk.SUNKEN, bd=1)
        info_frame.pack(padx=20, pady=20, fill=tk.X)
        
        info_text = "ℹ️ Note: Bundles are only charged when used in a call. Sales detector runs during the call and politely ends sales calls."
        tk.Label(
            info_frame,
            text=info_text,
            font=('Segoe UI', 9),
            bg='#2c3e50',
            fg='#f39c12',
            wraplength=520,
            justify=tk.LEFT
        ).pack(padx=10, pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(popup, bg='#2c3e50')
        button_frame.pack(pady=20)
        
        def save_settings():
            try:
                call_credits = float(call_entry.get())
                minute_credits = float(minute_entry.get())
                booking_credits = float(booking_entry.get())
                task_credits = float(task_entry.get())
                voice_credits = float(voice_entry.get())
                sales_credits = float(sales_entry.get())
                
                # Validate
                if call_credits < 0 or minute_credits < 0 or booking_credits < 0 or task_credits < 0 or voice_credits < 0 or sales_credits < 0:
                    self.log("❌ Credit values cannot be negative")
                    return
                
                # Save to database
                script_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(script_dir, "call_logs.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE billing_config 
                    SET credits_per_connected_call = ?,
                        credits_per_minute = ?,
                        credits_per_calendar_booking = ?,
                        credits_per_task = ?,
                        credits_per_advanced_voice = ?,
                        credits_per_sales_detection = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (call_credits, minute_credits, booking_credits, task_credits, voice_credits, sales_credits))
                
                conn.commit()
                conn.close()
                
                self.log(f"✅ Billing settings saved:")
                self.log(f"   📞 Connected call: {call_credits} credits")
                self.log(f"   ⏱️ Per minute: {minute_credits} credits")
                self.log(f"   📅 Calendar booking: {booking_credits} credits")
                self.log(f"   ✓ Task extraction: {task_credits} credits")
                self.log(f"   🎙️ Advanced voice: {voice_credits} credits")
                self.log(f"   🚫 Sales detection: {sales_credits} credits")
                
                popup.destroy()
                
            except ValueError:
                self.log("❌ Invalid number format. Please enter valid numbers.")
            except Exception as e:
                self.log(f"❌ Error saving billing settings: {e}")
        
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Settings",
            command=save_settings,
            bg='#27ae60',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            padx=30,
            pady=8
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=popup.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            padx=30,
            pady=8
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def show_voice_diagnostics(self):
        """Show voice provider diagnostics window"""
        popup = tk.Toplevel(self.root)
        popup.title("🔍 Voice Provider Diagnostics")
        popup.geometry("700x600")
        popup.configure(bg='#34495e')
        
        # Header
        header = tk.Label(
            popup,
            text="🔍 Voice Provider Diagnostics",
            font=('Segoe UI', 14, 'bold'),
            bg='#34495e',
            fg='white'
        )
        header.pack(pady=10)
        
        # Create scrollable text area for diagnostics
        text_frame = tk.Frame(popup, bg='#34495e')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        diag_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bg='#2c3e50',
            fg='white',
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        diag_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=diag_text.yview)
        
        def run_diagnostics():
            diag_text.delete('1.0', tk.END)
            diag_text.insert(tk.END, "🔄 Running voice provider diagnostics...\n\n")
            diag_text.update()
            
            try:
                import sqlite3
                conn = sqlite3.connect('phone_agent.db')
                cursor = conn.cursor()
                
                # Check PlayHT configuration
                diag_text.insert(tk.END, "━" * 60 + "\n")
                diag_text.insert(tk.END, "📊 PLAY.HT CONFIGURATION\n")
                diag_text.insert(tk.END, "━" * 60 + "\n\n")
                
                # Check if API credentials are set in code
                from vonage_agent import playht_api_key, playht_user_id
                if playht_api_key and playht_user_id:
                    diag_text.insert(tk.END, "✅ PlayHT API Key: Configured\n")
                    diag_text.insert(tk.END, f"✅ PlayHT User ID: {playht_user_id[:10]}...\n\n")
                else:
                    diag_text.insert(tk.END, "❌ PlayHT API Key: NOT CONFIGURED\n")
                    diag_text.insert(tk.END, "❌ PlayHT User ID: NOT CONFIGURED\n")
                    diag_text.insert(tk.END, "⚠️  Set PLAYHT_API_KEY and PLAYHT_USER_ID in vonage_agent.py\n\n")
                
                # Check user voice provider settings
                cursor.execute('SELECT COUNT(*) FROM account_settings WHERE voice_provider = "playht"')
                playht_users = cursor.fetchone()[0]
                diag_text.insert(tk.END, f"👥 Users with PlayHT selected: {playht_users}\n\n")
                
                # Check recent calls with PlayHT
                cursor.execute('''
                    SELECT COUNT(*) FROM calls c
                    JOIN account_settings a ON c.user_id = a.user_id
                    WHERE a.voice_provider = "playht"
                ''')
                playht_calls = cursor.fetchone()[0]
                diag_text.insert(tk.END, f"📞 Total calls with PlayHT: {playht_calls}\n\n")
                
                # Check for common issues
                diag_text.insert(tk.END, "━" * 60 + "\n")
                diag_text.insert(tk.END, "🔍 COMMON ISSUES CHECK\n")
                diag_text.insert(tk.END, "━" * 60 + "\n\n")
                
                issues_found = False
                
                if not playht_api_key or not playht_user_id:
                    diag_text.insert(tk.END, "❌ ISSUE: PlayHT credentials not configured\n")
                    diag_text.insert(tk.END, "   FIX: Add PLAYHT_API_KEY and PLAYHT_USER_ID in vonage_agent.py\n\n")
                    issues_found = True
                
                # Check if playht_voice_id column exists
                cursor.execute("PRAGMA table_info(account_settings)")
                columns = [col[1] for col in cursor.fetchall()]
                if 'playht_voice_id' not in columns:
                    diag_text.insert(tk.END, "❌ ISSUE: Database missing playht_voice_id column\n")
                    diag_text.insert(tk.END, "   FIX: Restart server to auto-create column\n\n")
                    issues_found = True
                
                if not issues_found:
                    diag_text.insert(tk.END, "✅ No configuration issues found!\n\n")
                
                # Voice provider summary
                diag_text.insert(tk.END, "━" * 60 + "\n")
                diag_text.insert(tk.END, "📊 ALL VOICE PROVIDERS\n")
                diag_text.insert(tk.END, "━" * 60 + "\n\n")
                
                cursor.execute('''
                    SELECT voice_provider, COUNT(*) 
                    FROM account_settings 
                    GROUP BY voice_provider
                ''')
                for provider, count in cursor.fetchall():
                    diag_text.insert(tk.END, f"  {provider or 'openai'}: {count} users\n")
                
                conn.close()
                
                diag_text.insert(tk.END, "\n✅ Diagnostics complete!\n")
                
            except Exception as e:
                diag_text.insert(tk.END, f"\n❌ Error running diagnostics: {e}\n")
                import traceback
                diag_text.insert(tk.END, f"\n{traceback.format_exc()}\n")
        
        # Run diagnostics button
        run_btn = tk.Button(
            popup,
            text="🔄 Run Diagnostics",
            command=run_diagnostics,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            padx=20,
            pady=8
        )
        run_btn.pack(pady=10)
        
        # Run diagnostics on open
        run_diagnostics()
    
    def show_live_diagnostics(self):
        """Show live call diagnostics with timing breakdown"""
        popup = tk.Toplevel(self.root)
        popup.title("📊 Live Call Diagnostics")
        popup.geometry("900x700")
        popup.configure(bg='#2c3e50')
        
        # Header
        header = tk.Label(
            popup,
            text="📊 Live Call Diagnostics - Real-Time Timing Analysis",
            font=('Segoe UI', 14, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=15
        )
        header.pack()
        
        # Info text
        info = tk.Label(
            popup,
            text="This analyzes your most recent phone call and shows where delays are occurring",
            font=('Segoe UI', 9),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        info.pack()
        
        # Diagnostic output
        diag_frame = tk.Frame(popup, bg='#2c3e50', padx=20, pady=10)
        diag_frame.pack(fill=tk.BOTH, expand=True)
        
        diag_text = scrolledtext.ScrolledText(
            diag_frame,
            wrap=tk.WORD,
            width=100,
            height=30,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#00ff00',
            insertbackground='white'
        )
        diag_text.pack(fill=tk.BOTH, expand=True)
        
        def analyze_call():
            """Analyze the most recent call from logs"""
            diag_text.delete('1.0', tk.END)
            diag_text.insert(tk.END, "Analyzing most recent call...\n\n")
            diag_text.update()
            
            try:
                import re
                from datetime import datetime
                
                # Read log file
                log_file = 'server_startup.log'
                if not os.path.exists(log_file):
                    diag_text.insert(tk.END, "❌ Log file not found. Make sure server is running.\n")
                    return
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                
                # Find all call UUIDs
                call_pattern = r'\[([a-f0-9-]{36})\]'
                calls = list(set(re.findall(call_pattern, log_content)))
                
                if not calls:
                    diag_text.insert(tk.END, "❌ No calls found in logs.\n")
                    diag_text.insert(tk.END, "   Make a test call first, then run diagnostics.\n")
                    return
                
                # Get the last call
                last_call = calls[-1]
                diag_text.insert(tk.END, f"📞 Call UUID: {last_call}\n")
                diag_text.insert(tk.END, "="*80 + "\n\n")
                
                # Extract lines for this call
                call_lines = [line for line in log_content.split('\n') if last_call in line]
                
                # Parse events with timestamps
                events = []
                for line in call_lines:
                    timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                    if not timestamp_match:
                        continue
                    
                    ts_str = timestamp_match.group(1)
                    try:
                        ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S,%f')
                    except:
                        continue
                    
                    # Capture key events
                    if 'VAD:' in line or 'VAD silence' in line:
                        match = re.search(r'silence=(\d+)ms', line)
                        if match:
                            events.append(('vad_configured', ts, int(match.group(1)), line))
                    elif 'Text delta:' in line:
                        match = re.search(r'Text delta: (\d+) chars', line)
                        if match:
                            events.append(('text_delta', ts, int(match.group(1)), line))
                    elif 'INSTANT:' in line or 'EARLY GEN' in line:
                        match = re.search(r'started at (\d+) chars', line)
                        if match:
                            events.append(('early_gen', ts, int(match.group(1)), line))
                    elif 'ElevenLabs' in line and 'generated' in line:
                        match = re.search(r'in (\d+)ms', line)
                        if match:
                            events.append(('elevenlabs', ts, int(match.group(1)), line))
                    elif 'TTS' in line and ('generated' in line or 'complete' in line):
                        match = re.search(r'in (\d+)ms', line)
                        if match:
                            events.append(('tts', ts, int(match.group(1)), line))
                    elif 'TEXT DONE' in line:
                        events.append(('text_done', ts, None, line))
                
                if not events:
                    diag_text.insert(tk.END, "⚠️  No timing events found for this call.\n\n")
                    diag_text.insert(tk.END, "Recent call activity:\n")
                    for line in call_lines[-20:]:
                        diag_text.insert(tk.END, f"  {line}\n")
                    return
                
                # Display timeline
                diag_text.insert(tk.END, "⏱️  EVENT TIMELINE\n")
                diag_text.insert(tk.END, "="*80 + "\n\n")
                
                start_time = events[0][1]
                timing_data = {
                    'vad_ms': None,
                    'tts_ms': None,
                    'early_gen': False,
                    'early_gen_chars': 0
                }
                
                for event_type, timestamp, value, line in events:
                    elapsed = (timestamp - start_time).total_seconds() * 1000
                    
                    if event_type == 'vad_configured':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | 🎤 VAD configured: {value}ms silence detection\n")
                        timing_data['vad_ms'] = value
                    elif event_type == 'text_delta':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | 📝 Text received: {value} characters\n")
                    elif event_type == 'early_gen':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | ⚡ EARLY GENERATION STARTED at {value} chars!\n")
                        timing_data['early_gen'] = True
                        timing_data['early_gen_chars'] = value
                    elif event_type == 'text_done':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | ✅ Text generation complete\n")
                    elif event_type == 'tts':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | 🔊 TTS: {value}ms\n")
                        timing_data['tts_ms'] = value
                    elif event_type == 'elevenlabs':
                        diag_text.insert(tk.END, f"+{elapsed:6.0f}ms | 🔊 ElevenLabs TTS: {value}ms\n")
                        timing_data['tts_ms'] = value
                
                # Analysis
                diag_text.insert(tk.END, "\n" + "="*80 + "\n")
                diag_text.insert(tk.END, "📊 PERFORMANCE ANALYSIS\n")
                diag_text.insert(tk.END, "="*80 + "\n\n")
                
                issues = []
                recommendations = []
                
                # Check VAD
                if timing_data['vad_ms']:
                    if timing_data['vad_ms'] < 300:
                        diag_text.insert(tk.END, f"⚠️  VAD: {timing_data['vad_ms']}ms - TOO FAST (may interrupt user)\n")
                        issues.append(f"VAD silence detection is {timing_data['vad_ms']}ms - this can cause AI to talk over user")
                        recommendations.append("Increase VAD silence_duration_ms to 400-500ms")
                    elif timing_data['vad_ms'] > 600:
                        diag_text.insert(tk.END, f"⚠️  VAD: {timing_data['vad_ms']}ms - TOO SLOW (user waits too long)\n")
                        issues.append(f"VAD silence detection is {timing_data['vad_ms']}ms - this makes response feel slow")
                        recommendations.append("Decrease VAD silence_duration_ms to 400ms")
                    else:
                        diag_text.insert(tk.END, f"✅ VAD: {timing_data['vad_ms']}ms - GOOD\n")
                
                # Check early generation
                if timing_data['early_gen']:
                    diag_text.insert(tk.END, f"✅ Early Generation: ACTIVE at {timing_data['early_gen_chars']} chars\n")
                else:
                    diag_text.insert(tk.END, f"❌ Early Generation: NOT TRIGGERED\n")
                    issues.append("Early audio generation did not trigger - TTS only started after full text")
                    recommendations.append("Enable early audio generation to start TTS while OpenAI is still generating text")
                
                # Check TTS speed
                if timing_data['tts_ms']:
                    if timing_data['tts_ms'] > 1200:
                        diag_text.insert(tk.END, f"❌ TTS Speed: {timing_data['tts_ms']}ms - VERY SLOW\n")
                        issues.append(f"TTS generation takes {timing_data['tts_ms']}ms - this is the main bottleneck")
                        recommendations.append("Consider switching to a faster TTS provider (OpenAI built-in voice or ElevenLabs)")
                    elif timing_data['tts_ms'] > 700:
                        diag_text.insert(tk.END, f"⚠️  TTS Speed: {timing_data['tts_ms']}ms - SLOW\n")
                        issues.append(f"TTS generation takes {timing_data['tts_ms']}ms")
                        recommendations.append("TTS is slower than optimal - consider OpenAI's built-in voice")
                    else:
                        diag_text.insert(tk.END, f"✅ TTS Speed: {timing_data['tts_ms']}ms - GOOD\n")
                
                # Store for AI analysis
                self.diagnostic_data = {
                    'issues': issues,
                    'recommendations': recommendations,
                    'timing_data': timing_data
                }
                
                diag_text.insert(tk.END, "\n" + "="*80 + "\n\n")
                
                if issues:
                    diag_text.insert(tk.END, "🔴 ISSUES FOUND:\n\n")
                    for i, issue in enumerate(issues, 1):
                        diag_text.insert(tk.END, f"  {i}. {issue}\n")
                else:
                    diag_text.insert(tk.END, "✅ No major issues detected!\n")
                
            except Exception as e:
                diag_text.insert(tk.END, f"\n❌ Error: {e}\n")
                import traceback
                diag_text.insert(tk.END, f"\n{traceback.format_exc()}\n")
        
        def ai_analysis():
            """Use DeepSeek AI to analyze the diagnostics"""
            if not hasattr(self, 'diagnostic_data'):
                diag_text.insert(tk.END, "\n❌ Please run diagnostics first!\n")
                return
            
            diag_text.insert(tk.END, "\n" + "="*80 + "\n")
            diag_text.insert(tk.END, "🤖 AI ANALYSIS (DeepSeek)\n")
            diag_text.insert(tk.END, "="*80 + "\n\n")
            diag_text.insert(tk.END, "Analyzing with DeepSeek AI...\n\n")
            diag_text.update()
            
            try:
                import requests
                
                # Read config to get DeepSeek API key
                try:
                    import sys
                    sys.path.insert(0, '.')
                    from vonage_agent import CONFIG
                    deepseek_key = CONFIG.get('DEEPSEEK_API_KEY', '')
                except:
                    deepseek_key = ''
                
                if not deepseek_key:
                    diag_text.insert(tk.END, "❌ DeepSeek API key not configured.\n")
                    return
                
                # Prepare prompt
                issues_text = "\n".join(f"- {issue}" for issue in self.diagnostic_data['issues'])
                timing_text = f"VAD: {self.diagnostic_data['timing_data'].get('vad_ms', 'N/A')}ms, TTS: {self.diagnostic_data['timing_data'].get('tts_ms', 'N/A')}ms, Early Gen: {self.diagnostic_data['timing_data'].get('early_gen', False)}"
                
                prompt = "You are analyzing voice call performance issues. Here is the diagnostic data:\n\n"
                prompt += f"TIMING DATA:\n{timing_text}\n\n"
                prompt += f"ISSUES FOUND:\n{issues_text}\n\n"
                prompt += "Please provide:\n"
                prompt += "1. A simple explanation (2-3 sentences) of what is causing the slow response\n"
                prompt += "2. The #1 most important fix to make it faster\n"
                prompt += "3. Expected improvement after the fix\n\n"
                prompt += "Keep the language simple and non-technical."
                
                response = requests.post(
                    'https://api.deepseek.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {deepseek_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'deepseek-chat',
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.7,
                        'max_tokens': 500
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content']
                    diag_text.insert(tk.END, ai_response + "\n\n")
                else:
                    diag_text.insert(tk.END, f"❌ DeepSeek API error: {response.status_code}\n")
                    diag_text.insert(tk.END, f"{response.text}\n")
                
            except Exception as e:
                diag_text.insert(tk.END, f"❌ AI analysis failed: {e}\n")
                import traceback
                diag_text.insert(tk.END, f"\n{traceback.format_exc()}\n")
        
        # Buttons frame
        btn_frame = tk.Frame(popup, bg='#2c3e50')
        btn_frame.pack(pady=10)
        
        analyze_btn = tk.Button(
            btn_frame,
            text="🔄 Analyze Last Call",
            command=analyze_call,
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            padx=20,
            pady=8
        )
        analyze_btn.pack(side=tk.LEFT, padx=5)
        
        ai_btn = tk.Button(
            btn_frame,
            text="🤖 AI Analysis (DeepSeek)",
            command=ai_analysis,
            bg='#9b59b6',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            padx=20,
            pady=8
        )
        ai_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-run on open
        analyze_call()

if __name__ == "__main__":
    # Check dependencies
    try:
        import psutil
    except ImportError:
        import tkinter.messagebox as messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing Dependency",
            "psutil module not installed.\n\nInstall with: pip install psutil"
        )
        sys.exit(1)
    
    root = tk.Tk()
    app = ServerControlGUI(root)
    root.mainloop()
