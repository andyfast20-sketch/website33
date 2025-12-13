"""
Vonage Agent Server Control - GUI
==================================
Simple GUI to start, stop, restart, and monitor the server
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import psutil
import os
import sys
import threading
import time
import webbrowser
import socket
import requests

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
        self.admin_dashboard_btn.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
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
                # Open log file for output
                with open(log_path, 'w') as log_file:
                    proc = subprocess.Popen(
                        [sys.executable, script_path],
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
                subprocess.Popen(
                    [sys.executable, script_path],
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
        title_label.pack(pady=(15, 10))
        
        # Loading label
        loading_label = tk.Label(
            popup,
            text="Loading numbers from Vonage...",
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
            loading_label.destroy()
            
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
            loading_label.destroy()
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
            
            close_btn = tk.Button(
                popup,
                text="Close",
                command=popup.destroy,
                bg='#e74c3c',
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                cursor='hand2',
                padx=20,
                pady=5
            )
            close_btn.pack(pady=10)
        
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
