"""
Master Launcher for WhatsApp Automation Suite
Allows launching either the 3-Window Desktop GUI or the Web Dashboard.
"""

import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("\n" + "="*65)
    print("   📱 WHATSAPP AUTOMATION SUITE - 3-WINDOW HUB")
    print("   • Window 1: Enter Phone Number & WhatsApp QR Connection")
    print("   • Window 2: Message Box (Text, Emojis, Formatting)")
    print("   • Window 3: Send Files (Photos & Videos with Previews)")
    print("="*65)
    print("\nSelect an interface to launch:")
    print("  [1] 🖥️  Launch Native Desktop App (CustomTkinter 3-Window GUI)")
    print("  [2] 🌐  Launch Web Dashboard (Browser / App Mode on http://127.0.0.1:5000)")
    print("  [3] ❌  Exit\n")

    choice = input("Enter choice (1, 2, or 3) [Default 1]: ").strip() or "1"

    if choice == "1":
        print("\n🚀 Starting Native Desktop App...")
        subprocess.run([sys.executable, os.path.join(base_dir, "app_gui.py")])
    elif choice == "2":
        print("\n🚀 Starting Web Dashboard on http://127.0.0.1:5000...")
        # Open in Edge or default browser
        try:
            import webbrowser
            threading_timer = subprocess.Popen(
                ["powershell", "-Command", "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000'"]
            )
        except Exception:
            pass
        subprocess.run([sys.executable, os.path.join(base_dir, "app_web.py")])
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()
