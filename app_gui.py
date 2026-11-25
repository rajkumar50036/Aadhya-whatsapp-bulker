"""
WhatsApp Automation Desktop App
Features a 3-Window / 3-Panel Architecture:
 - Window 1: Connect WhatsApp & Enter Phone Number
 - Window 2: Message Box (compose text, emojis, formatting)
 - Window 3: Send Files (Photos & Videos with previews)
Supports both Unified 3-Panel View and Pop-Out 3-Separate-Windows Mode.
"""

import os
import sys
import threading
import json
from datetime import datetime
from typing import List, Dict, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from whatsapp_engine import WhatsAppEngine

# Set appearance and color theme
ctk.set_appearance_mode("Dark") # "Dark", "Light", or "System"
ctk.set_default_color_theme("blue") # "blue", "dark-blue", "green"

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

COUNTRY_CODES = [
    ("India (+91)", "91"),
    ("USA / Canada (+1)", "1"),
    ("United Kingdom (+44)", "44"),
    ("United Arab Emirates (+971)", "971"),
    ("Saudi Arabia (+966)", "966"),
    ("Australia (+61)", "61"),
    ("Germany (+49)", "49"),
    ("France (+33)", "33"),
    ("Pakistan (+92)", "92"),
    ("Bangladesh (+880)", "880"),
    ("Singapore (+65)", "65"),
    ("Malaysia (+60)", "60"),
    ("Brazil (+55)", "55"),
    ("South Africa (+27)", "27"),
    ("Other (Manual)", "")
]

TEMPLATES = {
    "Select Template...": "",
    "Welcome Greeting": "Hello! Thank you for connecting with us. How can we assist you today?",
    "Photo / Video Share": "Hi! Please find attached the photos and videos you requested. Let me know if you need any more details!",
    "Invoice / Order Update": "Dear Customer, your order details and invoice have been processed. Please review the attached document.",
    "Appointment Reminder": "Friendly reminder: We have an upcoming scheduled appointment. Looking forward to speaking with you!"
}


class WhatsAppDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Aadhya WhatsApp Bulker - 3-Window Hub")
        self.geometry("1280x820")
        self.minsize(1050, 700)

        # Initialize WhatsApp Engine
        self.engine = WhatsAppEngine(browser="edge")
        self.engine.on_log = self._on_engine_log
        self.engine.on_status_change = self._on_engine_status

        # Data State
        self.attached_files: List[Dict[str, str]] = [] # [{path, type, size, name}]
        self.recent_numbers: List[str] = self._load_history()
        self.separate_windows_mode = False
        self.win1_window: Optional[ctk.CTkToplevel] = None
        self.win2_window: Optional[ctk.CTkToplevel] = None
        self.win3_window: Optional[ctk.CTkToplevel] = None

        self._build_ui()

    def _load_history(self) -> List[str]:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self, phone: str):
        if phone and phone not in self.recent_numbers:
            self.recent_numbers.insert(0, phone)
            self.recent_numbers = self.recent_numbers[:10]
            try:
                with open(HISTORY_FILE, "w") as f:
                    json.dump(self.recent_numbers, f)
            except Exception:
                pass

    def _build_ui(self):
        # 1. Top Header Bar
        self.header_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color=("#1f2937", "#111827"))
        self.header_frame.pack(side="top", fill="x")

        # App Title & Icon
        title_label = ctk.CTkLabel(
            self.header_frame, 
            text="📱 Aadhya WhatsApp Bulker",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=12)

        # WhatsApp Status Pill
        self.status_pill = ctk.CTkButton(
            self.header_frame,
            text="⚪ Status: Disconnected",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            text_color="#f3f4f6",
            height=32,
            corner_radius=16,
            command=self._check_status
        )
        self.status_pill.pack(side="left", padx=10, pady=12)

        # Connect WhatsApp Button
        self.connect_btn = ctk.CTkButton(
            self.header_frame,
            text="🔗 Connect WhatsApp Web (QR)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=32,
            corner_radius=8,
            command=self._start_whatsapp_session
        )
        self.connect_btn.pack(side="left", padx=10, pady=12)

        # Window Mode Switcher Button
        self.mode_toggle_btn = ctk.CTkButton(
            self.header_frame,
            text="🪟 Pop-Out 3 Separate Windows",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=32,
            corner_radius=8,
            command=self._toggle_window_mode
        )
        self.mode_toggle_btn.pack(side="right", padx=20, pady=12)

        # 2. Main 3-Window Container Frame
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="top", fill="both", expand=True, padx=16, pady=12)

        # Configure 3 equal columns
        self.main_container.grid_columnconfigure(0, weight=1, uniform="cols")
        self.main_container.grid_columnconfigure(1, weight=1, uniform="cols")
        self.main_container.grid_columnconfigure(2, weight=1, uniform="cols")
        self.main_container.grid_rowconfigure(0, weight=1)

        # Window 1: Phone Number & Connection Panel
        self.frame_win1 = self._create_win1_content(self.main_container)
        self.frame_win1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        # Window 2: Message Box Panel
        self.frame_win2 = self._create_win2_content(self.main_container)
        self.frame_win2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        # Window 3: Send Files (Photos & Videos) Panel
        self.frame_win3 = self._create_win3_content(self.main_container)
        self.frame_win3.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)

        # 3. Bottom Action Bar & Logs Area
        self.footer_frame = ctk.CTkFrame(self, height=160, corner_radius=12, fg_color=("#1e293b", "#0f172a"))
        self.footer_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 12))

        # Action Button & Progress
        act_row = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        act_row.pack(fill="x", padx=15, pady=(10, 6))

        self.send_btn = ctk.CTkButton(
            act_row,
            text="🚀 SEND MESSAGE & FILES TO WHATSAPP",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=46,
            corner_radius=8,
            command=self._on_send_clicked
        )
        self.send_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(act_row, height=12, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", fill="x", expand=False)
        self.progress_bar.configure(width=200)

        # Live Console Log Box
        self.log_textbox = ctk.CTkTextbox(
            self.footer_frame, 
            height=70, 
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#030712",
            text_color="#94a3b8"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(2, 10))
        self._append_log("System initialized. Connect WhatsApp Web or enter phone number to begin.")

    # -------------------------------------------------------------
    # WINDOW 1: PHONE NUMBER & CONNECTION
    # -------------------------------------------------------------
    def _create_win1_content(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#273549", "#1e293b"))
        
        # Header Badge
        header = ctk.CTkFrame(card, height=44, corner_radius=8, fg_color="#334155")
        header.pack(fill="x", padx=10, pady=10)
        title = ctk.CTkLabel(
            header, 
            text="📞 WINDOW 1: PHONE NUMBER",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        title.pack(side="left", padx=12, pady=8)

        # Connection Box
        conn_box = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8)
        conn_box.pack(fill="x", padx=12, pady=(0, 10))

        conn_lbl = ctk.CTkLabel(conn_box, text="WhatsApp Session Status:", font=ctk.CTkFont(size=12, weight="bold"))
        conn_lbl.pack(anchor="w", padx=10, pady=(8, 2))

        self.win1_status_lbl = ctk.CTkLabel(
            conn_box, 
            text="⚪ Not Connected (Click 'Connect' above)",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        )
        self.win1_status_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # Country Code Selector
        cc_lbl = ctk.CTkLabel(card, text="Country Code:", font=ctk.CTkFont(size=12, weight="bold"))
        cc_lbl.pack(anchor="w", padx=14, pady=(5, 2))

        self.cc_combo = ctk.CTkComboBox(
            card,
            values=[c[0] for c in COUNTRY_CODES],
            command=self._on_country_selected,
            height=34
        )
        self.cc_combo.set("India (+91)")
        self.cc_combo.pack(fill="x", padx=12, pady=(0, 8))

        # Phone Number Input
        phone_lbl = ctk.CTkLabel(card, text="Recipient Phone Number:", font=ctk.CTkFont(size=12, weight="bold"))
        phone_lbl.pack(anchor="w", padx=14, pady=(5, 2))

        self.phone_entry = ctk.CTkEntry(
            card,
            placeholder_text="Enter number (e.g. 9876543210)",
            height=38,
            font=ctk.CTkFont(size=14)
        )
        self.phone_entry.pack(fill="x", padx=12, pady=(0, 6))
        self.phone_entry.bind("<KeyRelease>", self._update_formatted_preview)

        # Live formatted display preview
        self.phone_preview_lbl = ctk.CTkLabel(
            card,
            text="WhatsApp Target: None",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#64748b"
        )
        self.phone_preview_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # Recent Numbers / History
        hist_lbl = ctk.CTkLabel(card, text="Recent Numbers / History:", font=ctk.CTkFont(size=12, weight="bold"))
        hist_lbl.pack(anchor="w", padx=14, pady=(5, 2))

        recent_vals = self.recent_numbers if self.recent_numbers else ["No recent numbers"]
        self.history_combo = ctk.CTkComboBox(
            card,
            values=recent_vals,
            command=self._on_history_selected,
            height=32
        )
        self.history_combo.set("Select from history...")
        self.history_combo.pack(fill="x", padx=12, pady=(0, 14))

        # Helpful hint box
        hint_box = ctk.CTkFrame(card, fg_color="#1e293b", corner_radius=6)
        hint_box.pack(fill="both", expand=True, padx=12, pady=10)
        hint_text = ctk.CTkLabel(
            hint_box,
            text="💡 Tip:\n• Always include the full phone number.\n• Country code is automatically attached.\n• Once you scan the QR code once, WhatsApp stays connected!",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            justify="left",
            wraplength=260
        )
        hint_text.pack(padx=10, pady=10, anchor="nw")

        return card

    # -------------------------------------------------------------
    # WINDOW 2: MESSAGE BOX
    # -------------------------------------------------------------
    def _create_win2_content(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#273549", "#1e293b"))

        # Header Badge
        header = ctk.CTkFrame(card, height=44, corner_radius=8, fg_color="#334155")
        header.pack(fill="x", padx=10, pady=10)
        title = ctk.CTkLabel(
            header, 
            text="✍️ WINDOW 2: MESSAGE BOX",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#a78bfa"
        )
        title.pack(side="left", padx=12, pady=8)

        # Quick Templates dropdown
        tpl_row = ctk.CTkFrame(card, fg_color="transparent")
        tpl_row.pack(fill="x", padx=12, pady=(0, 6))

        tpl_lbl = ctk.CTkLabel(tpl_row, text="Template:", font=ctk.CTkFont(size=12, weight="bold"))
        tpl_lbl.pack(side="left", padx=(2, 6))

        self.tpl_combo = ctk.CTkComboBox(
            tpl_row,
            values=list(TEMPLATES.keys()),
            command=self._on_template_selected,
            height=30
        )
        self.tpl_combo.set("Select Template...")
        self.tpl_combo.pack(side="left", fill="x", expand=True)

        # Formatting Toolbar
        toolbar = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=6, height=34)
        toolbar.pack(fill="x", padx=12, pady=(0, 6))

        fmt_bold = ctk.CTkButton(toolbar, text="B", width=30, height=26, font=ctk.CTkFont(weight="bold"), command=lambda: self._insert_format("*"))
        fmt_bold.pack(side="left", padx=3, pady=3)
        fmt_italic = ctk.CTkButton(toolbar, text="I", width=30, height=26, font=ctk.CTkFont(slant="italic"), command=lambda: self._insert_format("_"))
        fmt_italic.pack(side="left", padx=3, pady=3)
        fmt_strike = ctk.CTkButton(toolbar, text="S", width=30, height=26, command=lambda: self._insert_format("~"))
        fmt_strike.pack(side="left", padx=3, pady=3)
        fmt_code = ctk.CTkButton(toolbar, text="< >", width=34, height=26, command=lambda: self._insert_format("```"))
        fmt_code.pack(side="left", padx=3, pady=3)

        # Emoji quick buttons
        for emoji in ["👍", "❤️", "😊", "🙏", "🎉", "📸", "🎥"]:
            ebtn = ctk.CTkButton(
                toolbar, 
                text=emoji, 
                width=28, 
                height=26, 
                fg_color="transparent", 
                hover_color="#334155",
                command=lambda em=emoji: self._insert_text(em)
            )
            ebtn.pack(side="left", padx=1, pady=3)

        # Main Multiline Message Box
        self.message_box = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            fg_color="#0f172a"
        )
        self.message_box.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.message_box.insert("0.0", "Hello! Sending you this message along with the requested photos and videos.")
        self.message_box.bind("<KeyRelease>", self._update_message_counters)

        # Bottom Counter & Clear row
        bottom_row = ctk.CTkFrame(card, fg_color="transparent")
        bottom_row.pack(fill="x", padx=12, pady=(0, 10))

        self.char_count_lbl = ctk.CTkLabel(
            bottom_row, 
            text="Characters: 0 | Words: 0",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        self.char_count_lbl.pack(side="left", padx=4)

        clear_msg_btn = ctk.CTkButton(
            bottom_row,
            text="Clear Text",
            font=ctk.CTkFont(size=11),
            fg_color="#475569",
            hover_color="#334155",
            width=70,
            height=24,
            command=lambda: self.message_box.delete("0.0", "end")
        )
        clear_msg_btn.pack(side="right", padx=4)

        self._update_message_counters(None)
        return card

    # -------------------------------------------------------------
    # WINDOW 3: SEND FILES (PHOTOS & VIDEOS)
    # -------------------------------------------------------------
    def _create_win3_content(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#273549", "#1e293b"))

        # Header Badge
        header = ctk.CTkFrame(card, height=44, corner_radius=8, fg_color="#334155")
        header.pack(fill="x", padx=10, pady=10)
        title = ctk.CTkLabel(
            header, 
            text="📁 WINDOW 3: SEND FILES (MEDIA)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#34d399"
        )
        title.pack(side="left", padx=12, pady=8)

        # Action Buttons Row (Add Photos, Add Videos, Add Docs)
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 8))

        add_photo_btn = ctk.CTkButton(
            btn_row,
            text="📷 Add Photos",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            command=self._browse_photos
        )
        add_photo_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        add_video_btn = ctk.CTkButton(
            btn_row,
            text="🎥 Add Videos",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            height=32,
            command=self._browse_videos
        )
        add_video_btn.pack(side="left", fill="x", expand=True, padx=4)

        add_doc_btn = ctk.CTkButton(
            btn_row,
            text="📄 Any File",
            font=ctk.CTkFont(size=12),
            fg_color="#475569",
            hover_color="#334155",
            width=70,
            height=32,
            command=self._browse_all_files
        )
        add_doc_btn.pack(side="left", padx=(4, 0))

        # Files Count & Clear Bar
        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=14, pady=(2, 6))

        self.files_count_lbl = ctk.CTkLabel(
            info_row,
            text="Attached: 0 files (0 MB)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8"
        )
        self.files_count_lbl.pack(side="left")

        clear_files_btn = ctk.CTkButton(
            info_row,
            text="Remove All",
            font=ctk.CTkFont(size=11),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            width=80,
            height=22,
            command=self._clear_all_files
        )
        clear_files_btn.pack(side="right")

        # Scrollable list of attached media
        self.files_scroll_frame = ctk.CTkScrollableFrame(
            card,
            corner_radius=8,
            fg_color="#0f172a"
        )
        self.files_scroll_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Image Thumbnail Preview Frame
        self.preview_frame = ctk.CTkFrame(card, height=90, fg_color="#1e293b", corner_radius=6)
        self.preview_frame.pack(fill="x", padx=12, pady=(0, 10))

        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Preview: No media selected",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#64748b"
        )
        self.preview_label.pack(pady=30)

        self._render_files_list()
        return card

    # -------------------------------------------------------------
    # EVENT HANDLERS & HELPERS
    # -------------------------------------------------------------
    def _on_country_selected(self, choice):
        self._update_formatted_preview(None)

    def _get_target_phone(self) -> str:
        code = ""
        for name, c in COUNTRY_CODES:
            if name == self.cc_combo.get():
                code = c
                break
        raw_number = self.phone_entry.get().strip()
        cleaned_num = "".join(filter(str.isdigit, raw_number))
        
        # If user typed leading 0 or duplicate country code
        if code and cleaned_num.startswith(code):
            return cleaned_num
        elif code:
            if cleaned_num.startswith("0"):
                cleaned_num = cleaned_num[1:]
            return f"{code}{cleaned_num}"
        return cleaned_num

    def _update_formatted_preview(self, event):
        target = self._get_target_phone()
        if target:
            self.phone_preview_lbl.configure(
                text=f"WhatsApp Target: +{target}",
                text_color="#34d399"
            )
        else:
            self.phone_preview_lbl.configure(
                text="WhatsApp Target: None",
                text_color="#64748b"
            )

    def _on_history_selected(self, phone):
        if phone and phone != "Select from history..." and phone != "No recent numbers":
            self.phone_entry.delete(0, "end")
            self.phone_entry.insert(0, phone)
            self._update_formatted_preview(None)

    def _on_template_selected(self, choice):
        if choice in TEMPLATES and TEMPLATES[choice]:
            self.message_box.delete("0.0", "end")
            self.message_box.insert("0.0", TEMPLATES[choice])
            self._update_message_counters(None)

    def _insert_format(self, marker: str):
        try:
            sel_text = self.message_box.get("sel.first", "sel.last")
            self.message_box.delete("sel.first", "sel.last")
            self.message_box.insert("insert", f"{marker}{sel_text}{marker}")
        except Exception:
            self.message_box.insert("insert", f"{marker}text{marker}")
        self._update_message_counters(None)

    def _insert_text(self, text: str):
        self.message_box.insert("insert", text)
        self._update_message_counters(None)

    def _update_message_counters(self, event):
        content = self.message_box.get("0.0", "end-1c")
        chars = len(content)
        words = len(content.split())
        self.char_count_lbl.configure(text=f"Characters: {chars} | Words: {words}")

    # File Pickers
    def _browse_photos(self):
        paths = filedialog.askopenfilenames(
            title="Select Photos to Send",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.webp;*.bmp")]
        )
        for p in paths:
            self._add_file(p, "PHOTO")

    def _browse_videos(self):
        paths = filedialog.askopenfilenames(
            title="Select Videos to Send",
            filetypes=[("Video Files", "*.mp4;*.mov;*.avi;*.mkv;*.3gp;*.webm")]
        )
        for p in paths:
            self._add_file(p, "VIDEO")

    def _browse_all_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Any Files to Send",
            filetypes=[("All Files", "*.*")]
        )
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            ftype = "PHOTO" if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else "VIDEO" if ext in ['.mp4', '.mov', '.avi', '.mkv', '.3gp'] else "DOCUMENT"
            self._add_file(p, ftype)

    def _add_file(self, path: str, ftype: str):
        if any(f["path"] == path for f in self.attached_files):
            return
        size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
        size_mb = size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.1f} KB"
        
        self.attached_files.append({
            "path": path,
            "type": ftype,
            "size": size_str,
            "bytes": size_bytes,
            "name": os.path.basename(path)
        })
        self._render_files_list()

    def _remove_file(self, path: str):
        self.attached_files = [f for f in self.attached_files if f["path"] != path]
        self._render_files_list()

    def _clear_all_files(self):
        self.attached_files.clear()
        self._render_files_list()

    def _render_files_list(self):
        # Clear existing items
        for widget in self.files_scroll_frame.winfo_children():
            widget.destroy()

        total_bytes = sum(f.get("bytes", 0) for f in self.attached_files)
        total_mb = total_bytes / (1024 * 1024)
        self.files_count_lbl.configure(text=f"Attached: {len(self.attached_files)} files ({total_mb:.1f} MB)")

        if not self.attached_files:
            empty_lbl = ctk.CTkLabel(
                self.files_scroll_frame,
                text="No files attached yet.\nClick 'Add Photos' or 'Add Videos' above.",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#64748b"
            )
            empty_lbl.pack(pady=20)
            self._update_preview(None)
            return

        # Render list items
        for f in self.attached_files:
            item_row = ctk.CTkFrame(self.files_scroll_frame, fg_color="#1e293b", corner_radius=6)
            item_row.pack(fill="x", pady=2, padx=2)

            icon = "📷" if f["type"] == "PHOTO" else "🎥" if f["type"] == "VIDEO" else "📄"
            badge_color = "#0284c7" if f["type"] == "PHOTO" else "#7c3aed" if f["type"] == "VIDEO" else "#64748b"

            icon_lbl = ctk.CTkLabel(item_row, text=icon, font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(6, 2))

            name_lbl = ctk.CTkLabel(
                item_row, 
                text=f["name"], 
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w"
            )
            name_lbl.pack(side="left", fill="x", expand=True, padx=4)

            size_badge = ctk.CTkLabel(
                item_row, 
                text=f["size"], 
                font=ctk.CTkFont(size=10),
                text_color="#94a3b8"
            )
            size_badge.pack(side="left", padx=4)

            del_btn = ctk.CTkButton(
                item_row,
                text="✕",
                width=24,
                height=22,
                fg_color="#dc2626",
                hover_color="#b91c1c",
                command=lambda p=f["path"]: self._remove_file(p)
            )
            del_btn.pack(side="right", padx=4, pady=3)

        # Show preview of first photo if available
        first_photo = next((f["path"] for f in self.attached_files if f["type"] == "PHOTO"), None)
        self._update_preview(first_photo)

    def _update_preview(self, img_path: Optional[str]):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((120, 80))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                img_lbl = ctk.CTkLabel(self.preview_frame, image=ctk_img, text="")
                img_lbl.pack(side="left", padx=10, pady=5)
                desc = ctk.CTkLabel(
                    self.preview_frame,
                    text=f"Preview: {os.path.basename(img_path)}\nReady to send via WhatsApp",
                    font=ctk.CTkFont(size=11),
                    justify="left"
                )
                desc.pack(side="left", padx=5)
                return
            except Exception as e:
                print(f"Thumbnail error: {e}")

        lbl = ctk.CTkLabel(
            self.preview_frame,
            text="Preview: No image selected" if not self.attached_files else f"{len(self.attached_files)} media item(s) ready",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#64748b"
        )
        lbl.pack(pady=30)

    # -------------------------------------------------------------
    # 3-WINDOW POP-OUT MODE
    # -------------------------------------------------------------
    def _toggle_window_mode(self):
        if not self.separate_windows_mode:
            # Switch to 3 separate windows
            self.separate_windows_mode = True
            self.mode_toggle_btn.configure(text="📋 Return to Unified View")
            self._open_separate_windows()
        else:
            # Switch back to unified view
            self.separate_windows_mode = False
            self.mode_toggle_btn.configure(text="🪟 Pop-Out 3 Separate Windows")
            self._close_separate_windows()

    def _open_separate_windows(self):
        # Hide internal frames from main view
        self.frame_win1.grid_remove()
        self.frame_win2.grid_remove()
        self.frame_win3.grid_remove()

        # Show placeholder in center
        self.unified_placeholder = ctk.CTkLabel(
            self.main_container,
            text="🪟 3 Separate Windows are open on your screen!\n\n• Window 1: Phone Number & WhatsApp Connection\n• Window 2: Message Box\n• Window 3: Send Files (Photos & Videos)\n\nClick 'Return to Unified View' above anytime to merge them back.",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#94a3b8"
        )
        self.unified_placeholder.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=20, pady=40)

        # Create 3 Toplevel Floating Windows
        # Window 1
        self.win1_window = ctk.CTkToplevel(self)
        self.win1_window.title("Window 1: Enter Phone Number & WhatsApp Link")
        self.win1_window.geometry("380x600+50+100")
        self.win1_window.protocol("WM_DELETE_WINDOW", self._toggle_window_mode)
        self.frame_win1.reparent = self.win1_window
        self.frame_win1_sub = self._create_win1_content(self.win1_window)
        self.frame_win1_sub.pack(fill="both", expand=True, padx=8, pady=8)

        # Window 2
        self.win2_window = ctk.CTkToplevel(self)
        self.win2_window.title("Window 2: Message Box")
        self.win2_window.geometry("420x600+450+100")
        self.win2_window.protocol("WM_DELETE_WINDOW", self._toggle_window_mode)
        self.frame_win2_sub = self._create_win2_content(self.win2_window)
        self.frame_win2_sub.pack(fill="both", expand=True, padx=8, pady=8)

        # Window 3
        self.win3_window = ctk.CTkToplevel(self)
        self.win3_window.title("Window 3: Send Files (Videos & Photos)")
        self.win3_window.geometry("420x600+890+100")
        self.win3_window.protocol("WM_DELETE_WINDOW", self._toggle_window_mode)
        self.frame_win3_sub = self._create_win3_content(self.win3_window)
        self.frame_win3_sub.pack(fill="both", expand=True, padx=8, pady=8)

    def _close_separate_windows(self):
        if hasattr(self, 'unified_placeholder') and self.unified_placeholder:
            self.unified_placeholder.destroy()

        if self.win1_window:
            self.win1_window.destroy()
            self.win1_window = None
        if self.win2_window:
            self.win2_window.destroy()
            self.win2_window = None
        if self.win3_window:
            self.win3_window.destroy()
            self.win3_window = None

        # Re-attach and show unified frames
        self.frame_win1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.frame_win2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.frame_win3.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)

    # -------------------------------------------------------------
    # WHATSAPP ENGINE & SEND LOGIC
    # -------------------------------------------------------------
    def _start_whatsapp_session(self):
        self._append_log("Launching WhatsApp Web session in Edge/Chrome...")
        self.status_pill.configure(text="🟡 Starting WhatsApp...", fg_color="#d97706")
        self.engine.start_session(background=True)

    def _check_status(self):
        if self.engine.is_connected():
            messagebox.showinfo("WhatsApp Status", "🟢 WhatsApp Web is Connected and ready to send!")
        elif self.engine.status == "WAITING_FOR_QR":
            messagebox.showwarning("WhatsApp Status", "🟡 Please scan the QR code in the opened browser window.")
        else:
            messagebox.showinfo("WhatsApp Status", "⚪ WhatsApp is not connected. Click 'Connect WhatsApp Web (QR)'.")

    def _on_engine_log(self, text: str):
        self.after(0, lambda: self._append_log(text))

    def _on_engine_status(self, status: str, message: str):
        self.after(0, lambda: self._update_status_ui(status, message))

    def _update_status_ui(self, status: str, message: str):
        if status == "CONNECTED":
            self.status_pill.configure(text="🟢 Connected", fg_color="#059669")
            self.win1_status_lbl.configure(text="🟢 Connected & Ready", text_color="#34d399")
            self.connect_btn.configure(text="✅ WhatsApp Connected", fg_color="#047857")
        elif status == "WAITING_FOR_QR":
            self.status_pill.configure(text="🟡 Scan QR Code", fg_color="#d97706")
            self.win1_status_lbl.configure(text="🟡 Please scan QR Code in browser", text_color="#fbbf24")
        elif status == "STARTING":
            self.status_pill.configure(text="🟡 Loading...", fg_color="#d97706")
            self.win1_status_lbl.configure(text="🟡 Initializing browser session...", text_color="#fbbf24")
        else:
            self.status_pill.configure(text="⚪ Disconnected", fg_color="#374151")
            self.win1_status_lbl.configure(text="⚪ Disconnected", text_color="#94a3b8")
            self.connect_btn.configure(text="🔗 Connect WhatsApp Web (QR)", fg_color="#059669")

    def _append_log(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {text}\n"
        self.log_textbox.insert("end", formatted)
        self.log_textbox.see("end")

    def _on_send_clicked(self):
        phone = self._get_target_phone()
        if not phone or len(phone) < 7:
            messagebox.showerror("Error", "Please enter a valid phone number with country code in Window 1.")
            return

        message = self.message_box.get("0.0", "end-1c").strip()
        media_files = [f["path"] for f in self.attached_files]

        if not message and not media_files:
            messagebox.showerror("Error", "Please write a message in Window 2 or attach files in Window 3.")
            return

        # Save to history
        self._save_history(phone)
        self.history_combo.configure(values=self.recent_numbers)

        # Disable send button and start progress
        self.send_btn.configure(state="disabled", text="⏳ SENDING TO WHATSAPP...")
        self.progress_bar.start()

        def _worker():
            self._append_log(f"Starting send process to +{phone}...")
            result = self.engine.send(
                phone=phone,
                message=message,
                media_paths=media_files
            )
            self.after(0, lambda: self._on_send_completed(result))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _on_send_completed(self, result: Dict[str, any]):
        self.progress_bar.stop()
        self.progress_bar.set(1.0 if result.get("success") else 0)
        self.send_btn.configure(state="normal", text="🚀 SEND MESSAGE & FILES TO WHATSAPP")

        if result.get("success"):
            self._append_log(f"SUCCESS: {result.get('message')}")
            messagebox.showinfo("Success", f"✅ WhatsApp message and files sent successfully!\n\n{result.get('message')}")
        else:
            self._append_log(f"FAILED: {result.get('message')}")
            messagebox.showerror("Delivery Error", f"❌ Could not send WhatsApp message:\n\n{result.get('message')}")


if __name__ == "__main__":
    app = WhatsAppDesktopApp()
    app.mainloop()
