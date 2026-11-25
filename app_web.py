"""
WhatsApp Automation Web Suite
Provides a sleek, modern 3-Window / 3-Card web dashboard running on Flask:
 - Window 1: WhatsApp Connection & Enter Phone Number
 - Window 2: Message Box (Composer, emojis, formatting)
 - Window 3: Send Files (Photos & Videos drag-and-drop uploader)
"""

import os
import sys
import json
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from whatsapp_engine import WhatsAppEngine

app = Flask(__name__)
app.secret_key = "whatsapp_automation_studio_secret_2026_xyz"
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Multi-User WhatsApp Engine & Session Store
user_engines = {}      # mobile -> WhatsAppEngine
user_logs = {}         # mobile -> [str]
user_bulk_states = {}  # mobile -> dict

def get_current_user() -> Optional[str]:
    return session.get("user")

def get_user_profile_dir(user: str) -> str:
    path = os.path.join(BASE_DIR, "user_profiles", f"whatsapp_{user}")
    os.makedirs(path, exist_ok=True)
    # If legacy session profile exists and user profile is empty, copy over so existing linked number is preserved
    legacy_profile = os.path.join(BASE_DIR, "whatsapp_profile")
    if os.path.exists(legacy_profile) and not os.listdir(path):
        import shutil
        try:
            shutil.copytree(legacy_profile, path, dirs_exist_ok=True)
        except Exception:
            pass
    return path

def get_user_engine(user: str) -> WhatsAppEngine:
    if user not in user_engines:
        prof_dir = get_user_profile_dir(user)
        eng = WhatsAppEngine(profile_dir=prof_dir, browser="edge")
        
        if user not in user_logs:
            user_logs[user] = []
        
        def user_log_collector(text: str):
            timestamp = datetime.now().strftime("%H:%M:%S")
            user_logs[user].append(f"[{timestamp}] {text}")
            if len(user_logs[user]) > 100:
                user_logs[user].pop(0)

        eng.on_log = user_log_collector
        user_engines[user] = eng
    return user_engines[user]

def get_user_logs(user: str) -> list:
    if user not in user_logs:
        user_logs[user] = []
    return user_logs[user]

def append_user_log(user: str, text: str):
    logs = get_user_logs(user)
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {text}")
    if len(logs) > 100:
        logs.pop(0)

def get_user_bulk_state(user: str) -> dict:
    if user not in user_bulk_states:
        user_bulk_states[user] = {
            "is_running": False,
            "current": 0,
            "total": 0,
            "sent": 0,
            "failed": 0,
            "percent": 0,
            "last_phone": "",
            "last_status": ""
        }
    return user_bulk_states[user]

def get_user_history_file(user: str) -> str:
    return os.path.join(BASE_DIR, "user_profiles", f"history_{user}.json")

def get_user_chat_history_file(user: str) -> str:
    return os.path.join(BASE_DIR, "user_profiles", f"chat_history_{user}.json")

def load_user_chat_history(user: str) -> list:
    fpath = get_user_chat_history_file(user)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def record_chat_history(user: str, phone: str, message: str, files: list, success: bool, error: str = ""):
    if not user or not phone:
        return
    history = load_user_chat_history(user)
    
    file_names = [os.path.basename(f) for f in files] if files else []
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_display": datetime.now().strftime("%I:%M %p"),
        "date_display": datetime.now().strftime("%b %d, %Y"),
        "phone": phone,
        "message": (message[:75] + "...") if len(message) > 75 else message if message else "(Media file)",
        "full_message": message,
        "files_count": len(files) if files else 0,
        "files_names": file_names,
        "status": "SENT" if success else "FAILED",
        "error": error
    }
    history.insert(0, record)
    history = history[:500]  # keep last 500 records
    try:
        with open(get_user_chat_history_file(user), "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def load_user_history(user: str) -> list:
    fpath = get_user_history_file(user)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_user_history(user: str, phone: str):
    if not phone or not user:
        return
    history = load_user_history(user)
    if phone not in history:
        history.insert(0, phone)
        history = history[:10]
        try:
            with open(get_user_history_file(user), "w") as f:
                json.dump(history, f)
        except Exception:
            pass

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def normalize_mobile(phone: str) -> str:
    """Extracts digits from mobile number."""
    return "".join(filter(str.isdigit, str(phone)))

@app.before_request
def check_auth():
    # Whitelist routes that do not require login
    exempt_paths = ["/login", "/register", "/logout", "/api/auth/status", "/static"]
    for path in exempt_paths:
        if request.path.startswith(path):
            return None

    # Check if user is in session
    if not session.get("user"):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Unauthorized. Please login first."}), 401
        return redirect(url_for("login_page"))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        if session.get("user"):
            return redirect(url_for("index"))
        return render_template("login.html")

    # POST: handle login
    data = request.json or {}
    mobile = normalize_mobile(data.get("mobile", ""))
    password = str(data.get("password", "")).strip()

    if not mobile or len(mobile) < 7:
        return jsonify({"success": False, "message": "Please enter a valid mobile number."}), 400

    if not password:
        return jsonify({"success": False, "message": "Please enter your password."}), 400

    users = load_users()
    user_record = users.get(mobile)
    if not user_record:
        return jsonify({"success": False, "message": f"Mobile +{mobile} not found. Please click 'Sign Up' first."}), 404

    if not check_password_hash(user_record.get("password_hash", ""), password):
        return jsonify({"success": False, "message": "Incorrect password. Please try again."}), 401

    session["user"] = mobile
    append_user_log(mobile, f"👤 User +{mobile} logged in successfully.")

    # Automatically maintain and start personal WhatsApp Web session upon login
    engine = get_user_engine(mobile)
    if not engine.is_connected() and engine.status not in ["CONNECTING", "STARTING", "SCAN_QR", "WAITING_FOR_QR"]:
        threading.Thread(target=engine.start_session, kwargs={"background": False}, daemon=True).start()

    return jsonify({"success": True, "message": "Login successful!"})

@app.route("/register", methods=["POST"])
def register_user():
    data = request.json or {}
    mobile = normalize_mobile(data.get("mobile", ""))
    password = str(data.get("password", "")).strip()

    if not mobile or len(mobile) < 7:
        return jsonify({"success": False, "message": "Please enter a valid mobile number."}), 400

    if len(password) < 4:
        return jsonify({"success": False, "message": "Password must be at least 4 characters long."}), 400

    users = load_users()
    users[mobile] = {
        "mobile": mobile,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    session["user"] = mobile
    append_user_log(mobile, f"🎉 New user +{mobile} registered and logged in.")

    # Automatically maintain and start personal WhatsApp Web session upon registration
    engine = get_user_engine(mobile)
    if not engine.is_connected() and engine.status not in ["CONNECTING", "STARTING", "SCAN_QR", "WAITING_FOR_QR"]:
        threading.Thread(target=engine.start_session, kwargs={"background": False}, daemon=True).start()

    return jsonify({"success": True, "message": "Account created successfully! Logged in."})

@app.route("/logout")
def logout():
    user = session.pop("user", None)
    if user:
        if user in user_engines:
            try:
                append_user_log(user, f"👋 User +{user} logged out. Closing WhatsApp session.")
                user_engines[user].close_session()
                del user_engines[user]
            except Exception as e:
                print(f"Error closing session on logout: {e}")
    return redirect(url_for("login_page"))

@app.route("/api/auth/status")
def get_auth_status():
    users = load_users()
    current_user = session.get("user")
    return jsonify({
        "is_authenticated": bool(current_user),
        "user": current_user,
        "has_users": len(users) > 0
    })

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    user = get_current_user()
    if not user:
        return jsonify({"status": "DISCONNECTED", "message": "Not signed in", "is_connected": False, "qr_image": None})
    engine = get_user_engine(user)
    return jsonify({
        "status": engine.status,
        "message": engine.status_message,
        "is_connected": engine.is_connected(),
        "qr_image": engine.get_qr_image() if engine.status == "WAITING_FOR_QR" else None
    })

@app.route("/api/refresh_qr", methods=["POST"])
def refresh_qr():
    user = get_current_user()
    engine = get_user_engine(user)
    qr = engine.get_qr_image()
    return jsonify({"success": True, "qr_image": qr})

@app.route("/api/connect", methods=["POST"])
def connect_whatsapp():
    user = get_current_user()
    engine = get_user_engine(user)
    threading.Thread(target=engine.start_session, kwargs={"background": False}, daemon=True).start()
    return jsonify({"success": True, "message": f"Launching personal WhatsApp Web session for +{user}..."})

@app.route("/api/history", methods=["GET"])
def get_history():
    user = get_current_user()
    return jsonify({"history": load_user_history(user)})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    user = get_current_user()
    return jsonify({"logs": get_user_logs(user)})

@app.route("/api/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"success": False, "message": "No files received"}), 400

    uploaded = []
    files = request.files.getlist("files")
    for f in files:
        if f.filename:
            filename = secure_filename(f.filename)
            # Add timestamp to avoid collisions
            unique_name = f"{int(datetime.now().timestamp())}_{filename}"
            save_path = os.path.join(UPLOAD_DIR, unique_name)
            f.save(save_path)
            
            ext = os.path.splitext(filename)[1].lower()
            ftype = "PHOTO" if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else "VIDEO" if ext in ['.mp4', '.mov', '.avi', '.mkv', '.3gp'] else "DOCUMENT"
            size_bytes = os.path.getsize(save_path)
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.1f} KB"

            uploaded.append({
                "original_name": filename,
                "saved_path": save_path,
                "type": ftype,
                "size_str": size_str,
                "url": f"/uploads/{unique_name}"
            })

    return jsonify({"success": True, "files": uploaded})

@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/api/send", methods=["POST"])
def send_whatsapp():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    engine = get_user_engine(user)
    bulk_state = get_user_bulk_state(user)

    data = request.json or {}
    phone = data.get("phone", "").strip()
    phones = data.get("phones", [])
    message = data.get("message", "").strip()
    files = data.get("files", [])
    speed = float(data.get("speed", 2.0))
    is_bulk = data.get("is_bulk", False) or bool(data.get("phones"))

    # If single phone is passed in single mode
    if phone and not phones and not is_bulk:
        phones = [phone]

    if not phones:
        return jsonify({"success": False, "message": "Please enter at least one phone number"}), 400

    if not message and not files:
        return jsonify({"success": False, "message": "Message text or media files required"}), 400

    if not engine.is_connected():
        return jsonify({
            "success": False,
            "message": "Your personal WhatsApp is not connected! Please click 'Connect WhatsApp (QR)' and scan the code."
        }), 400

    # Single number mode (ONLY when NOT in bulk mode)
    if not is_bulk and len(phones) == 1:
        target = phones[0]
        save_user_history(user, target)
        append_user_log(user, f"⚡ Fast sending to +{target}...")
        result = engine.send_single(phone=target, message=message, media_paths=files)
        record_chat_history(user, target, message, files, result.get("success", False), result.get("message", ""))
        return jsonify(result)

    # Bulk numbers mode (ALWAYS runs as bulk campaign with live progress tracking)
    if bulk_state["is_running"]:
        return jsonify({"success": False, "message": "A bulk campaign is already running!"}), 400

    def progress_handler(info):
        bulk_state["current"] = info["current"]
        bulk_state["total"] = info["total"]
        bulk_state["sent"] = info["sent_count"]
        bulk_state["failed"] = info["failed_count"]
        bulk_state["percent"] = info["percent"]
        bulk_state["last_phone"] = info["phone"]
        bulk_state["last_status"] = "Success" if info["success"] else "Failed"
        # Automatically record to chat history
        record_chat_history(user, info["phone"], message, files, info["success"])

    def bulk_worker():
        bulk_state["is_running"] = True
        bulk_state["total"] = len(phones)
        bulk_state["current"] = 0
        bulk_state["sent"] = 0
        bulk_state["failed"] = 0
        bulk_state["percent"] = 0
        try:
            for p in phones:
                save_user_history(user, p)
            engine.send_bulk(
                phone_numbers=phones,
                message=message,
                media_paths=files,
                speed_delay=speed,
                progress_callback=progress_handler
            )
        finally:
            bulk_state["is_running"] = False

    threading.Thread(target=bulk_worker, daemon=True).start()
    return jsonify({
        "success": True,
        "is_bulk": True,
        "message": f"Bulk campaign started for {len(phones)} numbers"
    })

@app.route("/api/chat_history", methods=["GET"])
def get_chat_history():
    user = get_current_user()
    if not user:
        return jsonify({"history": []})
    return jsonify({"history": load_user_chat_history(user)})

@app.route("/api/clear_chat_history", methods=["POST"])
def clear_chat_history_endpoint():
    user = get_current_user()
    if user:
        fpath = get_user_chat_history_file(user)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
    return jsonify({"success": True, "message": "Chat history cleared."})

@app.route("/api/bulk_status", methods=["GET"])
def get_bulk_status():
    user = get_current_user()
    return jsonify(get_user_bulk_state(user))

@app.route("/api/stop_bulk", methods=["POST"])
def stop_bulk_campaign():
    user = get_current_user()
    engine = get_user_engine(user)
    engine.stop_bulk()
    get_user_bulk_state(user)["is_running"] = False
    return jsonify({"success": True, "message": "Bulk campaign stopped"})

if __name__ == "__main__":
    import socket
    local_ip = "127.0.0.1"
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        pass

    print("\n" + "="*60)
    print("🚀 Aadhya WhatsApp Bulker")
    print(f"👉 Local PC:        http://127.0.0.1:5000")
    print(f"👉 Mobile / Tablet: http://{local_ip}:5000 (Same Wi-Fi)")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
