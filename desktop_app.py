"""
Aadhya WhatsApp Bulker - Desktop Application Launcher
Bundles the complete automation suite into a standalone native Windows desktop application.
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request

# Ensure working directory is set to app root
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

def start_server():
    """Starts the Flask web application on port 5000."""
    try:
        from app_web import app
        # Run Flask silently in desktop mode
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")

def wait_for_server(timeout=15):
    """Waits until the server is responding on http://127.0.0.1:5000."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen("http://127.0.0.1:5000", timeout=1) as resp:
                if resp.status in (200, 302):
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

def open_desktop_window():
    """Opens the app in a standalone native desktop window (no URL bar, no tabs)."""
    url = "http://127.0.0.1:5000"
    
    # Try Edge App Mode (clean native desktop window)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    
    browser_exe = None
    for p in edge_paths:
        if os.path.exists(p):
            browser_exe = p
            break
            
    # Try Chrome if Edge not found
    if not browser_exe:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for p in chrome_paths:
            if os.path.exists(p):
                browser_exe = p
                break

    if browser_exe:
        # Launch as native standalone desktop app window
        cmd = [browser_exe, f"--app={url}", "--window-size=1280,850"]
        proc = subprocess.Popen(cmd)
        proc.wait()  # Wait until user closes the desktop window
    else:
        # Fallback to default browser
        import webbrowser
        webbrowser.open(url)
        # Keep alive until user exits
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    # Start Flask server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to be ready
    wait_for_server()
    
    # Open desktop app window (blocks until closed)
    open_desktop_window()
    
    # Clean exit
    sys.exit(0)

if __name__ == "__main__":
    main()
