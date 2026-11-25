# 🚀 Aadhya WhatsApp Bulker

A high-speed, modern WhatsApp automation suite featuring a **3-Window Hub** architecture to dispatch personalized messages, photos, videos, and documents to single and bulk numbers.

---

## 🪟 The 3-Window Architecture

| Window | Title | Description |
| :--- | :--- | :--- |
| **Window 1** | **Enter Phone Number** | • **Single Number Mode**: Country code picker + validation<br>• **Bulk Numbers Mode**: Paste customer lists or import `.csv`/`.txt` files<br>• Instant QR code linker for WhatsApp |
| **Window 2** | **Message Box** | • Multi-line composer with character & word counts<br>• Rich formatting: **Bold** (`*text*`), *Italic* (`_text_`), ~Strikethrough~, Code blocks<br>• Quick emoji bar & ready-to-use business message templates<br>• Text automatically attaches as media caption |
| **Window 3** | **Send Files (Media)** | • 📷 **Photos**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`<br>• 🎥 **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.3gp`<br>• 📄 **Documents**: `.pdf`, `.docx`, `.xlsx`, `.zip`, `.csv`<br>• Drag & drop uploader with media previews and file size indicators |

---

## 🌟 Key Features

- **Multi-User Account System**: Built-in **Login** and **Sign Up** authentication with encrypted passwords.
- **Session Persistence**: WhatsApp Web connections stay saved and running from login until explicit logout.
- **Saved Chat History**: Persistent log of every dispatched message with time, recipient, media count, status, and 1-click **Export to CSV**.
- **Real-Time Bulk Progress Bar**: Live progress indicators tracking Sent, Failed, and Last Recipient in real time.
- **Built-in Anti-Ban Safeguards**: Automated human jitter delays and cool-down pauses.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rajkumar50036/Aadhya-whatsapp-bulker.git
   cd Aadhya-whatsapp-bulker
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   - **Web Dashboard (Recommended)**:
     ```bash
     python app_web.py
     ```
     or double-click `run_web.bat`. Open your browser at `http://127.0.0.1:5000`.

   - **Native Desktop App**:
     ```bash
     python app_gui.py
     ```
     or double-click `run_desktop.bat`.

---

## 🔗 How to Connect

1. Open `http://127.0.0.1:5000` and create an account via **Sign Up**.
2. Click **Connect WhatsApp (QR)**.
3. Open WhatsApp on your phone $\rightarrow$ **Settings** > **Linked Devices** > **Link a Device**.
4. Scan the QR code. Once connected, your session is saved!

---

## 📄 License
MIT License. Created for business messaging automation.
