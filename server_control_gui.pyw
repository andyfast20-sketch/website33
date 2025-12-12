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
        self.ngrok_reset_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
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
                        except:
                            pass
                
                if not killed:
                    self.log("⚠️ No ngrok process found running")
                else:
                    time.sleep(1)
                    self.log("💡 Ngrok stopped. Start it manually with: ngrok http 5004")
                
                self.update_indicators()
                
            except Exception as e:
                self.log(f"❌ Error resetting ngrok: {e}")
        
        threading.Thread(target=_reset, daemon=True).start()
    
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
