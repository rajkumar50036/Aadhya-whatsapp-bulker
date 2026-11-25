"""
WhatsApp Automation Engine
High-Speed Bulk Messaging & Media Dispatcher (Photos, Videos, Documents)
Powered by Selenium (Microsoft Edge / Google Chrome)
"""

import os
import sys
import time
import urllib.parse
import threading
from typing import List, Callable, Optional, Dict, Any, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

class WhatsAppEngine:
    def __init__(self, profile_dir: Optional[str] = None, browser: str = "edge"):
        self.browser_name = browser.lower()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.profile_dir = profile_dir or os.path.join(base_dir, "whatsapp_profile")
        os.makedirs(self.profile_dir, exist_ok=True)
        
        self.driver: Optional[webdriver.Remote] = None
        self.is_running = False
        self._lock = threading.Lock()
        self.status = "DISCONNECTED" # DISCONNECTED, STARTING, WAITING_FOR_QR, CONNECTED, ERROR
        self.status_message = "Not connected"
        self.last_qr_image: Optional[str] = None
        self.is_sending = False
        self.cancel_bulk_requested = False
        
        # Callbacks
        self.on_status_change: Optional[Callable[[str, str], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None

    def log(self, text: str):
        print(f"[WhatsAppEngine] {text}")
        if self.on_log:
            try:
                self.on_log(text)
            except Exception as e:
                print(f"Log callback error: {e}")

    def set_status(self, status: str, message: str):
        self.status = status
        self.status_message = message
        self.log(f"Status: {status} ({message})")
        if self.on_status_change:
            try:
                self.on_status_change(status, message)
            except Exception as e:
                print(f"Status callback error: {e}")

    def _create_driver(self):
        """Initializes Edge or Chrome driver with persistent user profile."""
        self.log(f"Initializing {self.browser_name.upper()} with profile: {self.profile_dir}")
        
        if self.browser_name == "chrome":
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            opts = ChromeOptions()
            opts.add_argument(f"--user-data-dir={self.profile_dir}")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_argument("--disable-infobars")
            opts.add_argument("--start-maximized")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            driver = webdriver.Chrome(options=opts)
        else: # Default: Edge
            from selenium.webdriver.edge.options import Options as EdgeOptions
            opts = EdgeOptions()
            opts.add_argument(f"--user-data-dir={self.profile_dir}")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_argument("--disable-infobars")
            opts.add_argument("--start-maximized")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            driver = webdriver.Edge(options=opts)

        return driver

    def start_session(self, background: bool = False):
        """Starts browser and loads WhatsApp Web."""
        with self._lock:
            if self.driver is not None and self.is_running:
                self.log("Browser already active.")
                return True

            self.set_status("STARTING", "Launching browser...")

        def _worker():
            try:
                try:
                    self.driver = self._create_driver()
                except Exception as ex1:
                    self.log(f"Failed to start {self.browser_name}, switching browser: {ex1}")
                    self.browser_name = "chrome" if self.browser_name == "edge" else "edge"
                    self.driver = self._create_driver()

                self.is_running = True
                self.set_status("STARTING", "Loading WhatsApp Web...")
                self.driver.get("https://web.whatsapp.com")
                self._monitor_connection()
            except Exception as e:
                self.log(f"Error starting session: {e}")
                self.set_status("ERROR", f"Failed to start: {str(e)}")
                self.close_session()

        if background:
            threading.Thread(target=_worker, daemon=True).start()
        else:
            _worker()

    def _monitor_connection(self):
        """Monitors login state and extracts QR code."""
        self.log("Monitoring WhatsApp Web connection state...")
        while self.is_running and self.driver:
            try:
                # 1. Check if logged in
                chat_panes = self.driver.find_elements(By.XPATH, 
                    "//div[@id='pane-side'] | //div[@data-testid='chat-list'] | //header"
                )
                if chat_panes and any(p.is_displayed() for p in chat_panes):
                    if self.status != "CONNECTED":
                        self.set_status("CONNECTED", "WhatsApp is connected and ready to send messages!")
                    time.sleep(2)
                    continue

                # 2. Check for QR Code canvas
                qr_elements = self.driver.find_elements(By.XPATH,
                    "//div[@data-testid='qrcode']//canvas | "
                    "//canvas[@aria-label='Scan this QR code to link a device!'] | "
                    "//canvas[@aria-label='Scan me!'] | "
                    "//div[contains(@data-ref, '')]//canvas | "
                    "//canvas"
                )
                if qr_elements and any(q.is_displayed() for q in qr_elements):
                    self.get_qr_image()
                    if self.status != "WAITING_FOR_QR":
                        self.set_status("WAITING_FOR_QR", "Please scan the QR code to connect")
                    time.sleep(1.5)
                    continue

                if self.status not in ["CONNECTED", "WAITING_FOR_QR"]:
                    self.set_status("STARTING", "Syncing WhatsApp chats...")

                time.sleep(1.5)
            except WebDriverException:
                break
            except Exception as e:
                time.sleep(1.5)

        self.set_status("DISCONNECTED", "Browser closed")

    def get_qr_image(self) -> Optional[str]:
        """Returns base64 data URL of the WhatsApp Web QR code canvas."""
        if not self.driver or not self.is_running:
            return self.last_qr_image

        try:
            # Check if reload button exists and click it if expired
            reload_btns = self.driver.find_elements(By.XPATH,
                "//button[contains(., 'reload') or contains(., 'Reload')] | "
                "//span[@data-icon='refresh']/ancestor::button | "
                "//span[@data-icon='refresh'] | "
                "//div[contains(@class, 'reload') and @role='button']"
            )
            for rbtn in reload_btns:
                if rbtn.is_displayed():
                    self.log("QR code expired, clicking reload...")
                    rbtn.click()
                    time.sleep(1)
                    break

            qr_elements = self.driver.find_elements(By.XPATH,
                "//div[@data-testid='qrcode']//canvas | "
                "//canvas[@aria-label='Scan this QR code to link a device!'] | "
                "//canvas[@aria-label='Scan me!'] | "
                "//div[contains(@data-ref, '')]//canvas | "
                "//canvas"
            )
            for canvas in qr_elements:
                try:
                    w = canvas.size.get('width', 0)
                    h = canvas.size.get('height', 0)
                    if w < 50 or h < 50:
                        continue

                    # Direct JavaScript export
                    data_url = self.driver.execute_script("return arguments[0].toDataURL('image/png');", canvas)
                    if data_url and data_url.startswith("data:image"):
                        self.last_qr_image = data_url
                        return data_url

                    # Fallback screenshot
                    import base64
                    png_bytes = canvas.screenshot_as_png
                    if png_bytes and len(png_bytes) > 200:
                        b64 = base64.b64encode(png_bytes).decode('utf-8')
                        data_url = f"data:image/png;base64,{b64}"
                        self.last_qr_image = data_url
                        return data_url
                except Exception:
                    continue
        except Exception as e:
            pass

        return self.last_qr_image

    def is_connected(self) -> bool:
        return self.driver is not None and self.is_running and self.status == "CONNECTED"

    def clean_phone_number(self, phone: str) -> str:
        """Sanitizes phone number removing all non-digits."""
        return "".join(filter(str.isdigit, str(phone)))

    def send_single(self, phone: str, message: str = "", media_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        High-speed send function targeting < 2-second message delivery.
        Sends text message, photos, videos, and documents.
        """
        clean_phone = self.clean_phone_number(phone)
        if not clean_phone or len(clean_phone) < 7:
            return {"success": False, "message": f"Invalid phone: '{phone}'"}

        if not message.strip() and not media_paths:
            return {"success": False, "message": "No message text or files provided."}

        if not self.is_connected():
            return {"success": False, "message": "WhatsApp is not connected. Please scan QR code first."}

        t_start = time.time()
        try:
            self.log(f"⚡ Navigating to chat with +{clean_phone}...")
            # If no media, pass message directly in URL for instant prefill
            if message.strip() and not media_paths:
                encoded = urllib.parse.quote(message)
                self.driver.get(f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded}")
            else:
                self.driver.get(f"https://web.whatsapp.com/send?phone={clean_phone}")

            # Fast polling for chat readiness (checks every 0.2s, max 12s)
            chat_ready = False
            for _ in range(60):
                # Check for invalid phone popup
                popups = self.driver.find_elements(By.XPATH,
                    "//div[contains(text(), 'URL is invalid') or contains(text(), 'not on WhatsApp') or contains(text(), 'invalid')]"
                )
                if popups and any(p.is_displayed() for p in popups):
                    return {"success": False, "message": f"+{clean_phone} is not on WhatsApp"}

                # Check compose box or send button
                compose_boxes = self.driver.find_elements(By.XPATH,
                    "//footer//div[@contenteditable='true'] | "
                    "//div[@data-testid='conversation-compose-box-input'] | "
                    "//footer//span[contains(@data-icon, 'send')]"
                )
                if compose_boxes and any(b.is_displayed() for b in compose_boxes):
                    chat_ready = True
                    break
                time.sleep(0.2)

            if not chat_ready:
                return {"success": False, "message": f"Chat with +{clean_phone} timed out loading"}

            # Case A: Text Only - Immediate 1-step send (< 2 seconds total)
            if message.strip() and not media_paths:
                sent = self._click_send_button()
                elapsed = time.time() - t_start
                if sent:
                    self.log(f"✅ Text message sent to +{clean_phone} in {elapsed:.1f}s")
                    return {"success": True, "message": f"Sent to +{clean_phone} ({elapsed:.1f}s)"}
                else:
                    return {"success": False, "message": "Could not click send button"}

            # Case B: Media Files (Photos, Videos, Documents) + Optional Message
            media_sent_count = 0
            caption_was_attached = False

            for idx, fpath in enumerate(media_paths or []):
                abs_fpath = os.path.abspath(fpath)
                if not os.path.exists(abs_fpath):
                    self.log(f"File missing: {abs_fpath}")
                    continue

                # Use message as caption for the first photo/video
                file_caption = message if (idx == 0 and not caption_was_attached) else ""
                self.log(f"📤 Uploading: {os.path.basename(abs_fpath)}")
                ok, caption_applied = self._upload_media_file(abs_fpath, caption=file_caption)
                if ok:
                    media_sent_count += 1
                    if caption_applied:
                        caption_was_attached = True
                else:
                    self.log(f"Failed to upload: {os.path.basename(abs_fpath)}")

            # If user provided a message text but it was not attached as a caption
            # (e.g. sending documents where WhatsApp has no caption box),
            # send the text message directly into the chat!
            if message.strip() and not caption_was_attached and media_sent_count > 0:
                self.log("Dispatched message text separately (document has no caption box)")
                self._send_text_into_chat(message)

            elapsed = time.time() - t_start
            if media_sent_count > 0:
                self.log(f"✅ Sent {media_sent_count} file(s) to +{clean_phone} in {elapsed:.1f}s")
                return {"success": True, "message": f"Sent {media_sent_count} file(s) to +{clean_phone} ({elapsed:.1f}s)"}
            else:
                return {"success": False, "message": "Failed to upload media files"}

        except Exception as e:
            self.log(f"Send error for +{clean_phone}: {e}")
            return {"success": False, "message": str(e)}

    def _send_text_into_chat(self, text: str) -> bool:
        """Types and sends text into the active chat compose box."""
        try:
            res = self.driver.execute_script("""
                const box = document.querySelector("footer div[contenteditable='true'], div[data-testid='conversation-compose-box-input']");
                if (box) {
                    box.focus();
                    document.execCommand('insertText', false, arguments[0]);
                    return true;
                }
                return false;
            """, text)
            time.sleep(0.3)
            return self._click_send_button()
        except Exception as e:
            self.log(f"Could not send text in chat: {e}")
            return False

    def send(self, phone: str, message: str = "", media_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Wrapper for send_single."""
        return self.send_single(phone=phone, message=message, media_paths=media_paths)

    def _click_send_button(self) -> bool:
        """Clicks send button in footer using atomic JS with zero delay."""
        try:
            clicked = self.driver.execute_script("""
                const footer = document.querySelector("footer");
                if (footer) {
                    const sendBtn = footer.querySelector("button[aria-label*='Send'], div[role='button'][aria-label*='Send'], span[data-icon='send'], span[data-icon*='send']");
                    if (sendBtn) {
                        const clickable = sendBtn.closest("[role='button']") || sendBtn.closest("button") || sendBtn;
                        clickable.click();
                        return true;
                    }
                }
                return false;
            """)
            if clicked:
                return True
        except Exception:
            pass

        # Fallback with Enter key
        try:
            box = self.driver.find_element(By.XPATH, "//footer//div[@contenteditable='true']")
            box.send_keys(Keys.ENTER)
            return True
        except Exception:
            pass

        return False

    def _upload_media_file(self, file_path: str, caption: str = "") -> Tuple[bool, bool]:
        """
        Uploads and sends Photos, Videos, and Documents via WhatsApp Web.
        Uses dynamic file picker interception to engage WhatsApp's native media pipeline.
        Returns: (success: bool, caption_applied: bool)
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            self.log(f"File not found: {abs_path}")
            return False, False

        ext = os.path.splitext(abs_path)[1].lower()
        is_document = ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.zip', '.rar']
        menu_label = "Document" if is_document else "Photos & videos"

        try:
            # 1. Patch HTMLInputElement.prototype.click to catch dynamic input without opening native OS dialog
            self.driver.execute_script("""
                window._capturedFileInput = null;
                if (!window._origInputClick) {
                    window._origInputClick = HTMLInputElement.prototype.click;
                    HTMLInputElement.prototype.click = function() {
                        if (this.type === 'file') {
                            this.style.display = 'block';
                            this.style.opacity = '1';
                            this.style.position = 'fixed';
                            this.style.top = '0';
                            this.style.left = '0';
                            this.style.zIndex = '999999';
                            this.id = 'captured_whatsapp_file_input';
                            window._capturedFileInput = this;
                            return; // suppress OS native file dialog
                        }
                        return window._origInputClick.apply(this, arguments);
                    };
                }
            """)

            # 2. Click Attach button in footer
            attach_btns = self.driver.find_elements(By.XPATH, 
                "//footer//button[@aria-label='Attach'] | "
                "//footer//*[@aria-label='Attach'] | "
                "//footer//span[contains(@data-icon, 'plus')]"
            )
            if attach_btns:
                self.driver.execute_script("arguments[0].click();", attach_btns[0])
                time.sleep(0.5)

            # 3. Click menu item ("Photos & videos" or "Document")
            menu_btn = self.driver.find_elements(By.XPATH, f"//button[@aria-label='{menu_label}']")
            if menu_btn:
                self.driver.execute_script("arguments[0].click();", menu_btn[0])
                time.sleep(0.5)

            # 4. Find the captured dynamic input (or fallback to footer input)
            captured_inputs = self.driver.find_elements(By.ID, "captured_whatsapp_file_input")
            if not captured_inputs:
                captured_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")

            if not captured_inputs:
                self.log("Error: Could not locate file input on WhatsApp Web.")
                return False, False

            target_input = captured_inputs[0]
            self.log(f"Attaching file: {os.path.basename(abs_path)} (via {menu_label})")
            target_input.send_keys(abs_path)

            # 5. Wait for preview dialog, add caption if provided, and click green send button!
            t_start = time.time()
            send_clicked = False
            caption_added = False

            while time.time() - t_start < 15:
                # Add caption if provided
                if caption and not caption_added:
                    try:
                        res_caption = self.driver.execute_script("""
                            const box = document.querySelector("div:not(footer) div[contenteditable='true'], div[aria-label*='caption'], div[aria-placeholder*='caption']");
                            if (box && !box.closest("footer")) {
                                box.focus();
                                document.execCommand('insertText', false, arguments[0]);
                                return true;
                            }
                            return false;
                        """, caption)
                        if res_caption:
                            caption_added = True
                            self.log(f"Added caption: '{caption[:30]}...'")
                    except Exception:
                        pass

                # Click bottom-right send button (or elementFromPoint / aria-label='Send 1 selected' / aria-label='Send')
                try:
                    res_send = self.driver.execute_script("""
                        const w = window.innerWidth;
                        const h = window.innerHeight;
                        // First try elementFromPoint at bottom right
                        const pt = document.elementFromPoint(w - 50, h - 50);
                        if (pt) {
                            const btn = pt.closest("[role='button']") || pt.closest("button");
                            if (btn && !btn.closest("footer")) {
                                btn.click();
                                return { clicked: true, label: btn.getAttribute('aria-label') || 'point-btn' };
                            }
                        }

                        // Fallback to searching all preview buttons
                        const elements = Array.from(document.querySelectorAll("div[role='button'], button, span[data-icon='send'], span[data-icon*='send']"));
                        for (const el of elements) {
                            if (el.closest("footer")) continue;
                            const label = (el.getAttribute("aria-label") || "").toLowerCase();
                            const icon = (el.getAttribute("data-icon") || "").toLowerCase();
                            const hasSendIcon = el.querySelector("span[data-icon*='send']") !== null;
                            
                            if (label.includes("send") || label.includes("selected") || icon.includes("send") || hasSendIcon) {
                                const btn = el.closest("[role='button']") || el.closest("button") || el;
                                btn.click();
                                return { clicked: true, label: el.getAttribute("aria-label") || icon || "send-btn" };
                            }
                        }
                        return { clicked: false };
                    """)

                    if res_send and res_send.get("clicked"):
                        self.log(f"✅ Clicked media preview send button: '{res_send.get('label')}'")
                        send_clicked = True
                        break
                except Exception:
                    pass

                time.sleep(0.3)

            # Fallback if atomic click didn't trigger
            if not send_clicked:
                try:
                    active = self.driver.switch_to.active_element
                    active.send_keys(Keys.ENTER)
                    send_clicked = True
                    self.log("Dispatched Enter key to send media preview")
                except Exception as ex:
                    self.log(f"Enter fallback failed: {ex}")

            # Wait for preview dialog to finish sending and close
            for _ in range(25):
                time.sleep(0.2)
                dialog_open = self.driver.execute_script("""
                    const el = document.querySelector("div:not(footer) [role='button'][aria-label*='Send'], div:not(footer) [role='button'][aria-label*='selected']");
                    return el !== null;
                """)
                if not dialog_open:
                    break

            return send_clicked, caption_added

        except Exception as e:
            self.log(f"Error during media upload: {e}")
            return False, False

    def send_bulk(
        self,
        phone_numbers: List[str],
        message: str = "",
        media_paths: Optional[List[str]] = None,
        speed_delay: float = 2.0,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Sends messages and files to a bulk list of customer phone numbers.
        speed_delay: pause between customers (default 2.0 seconds).
        """
        self.is_sending = True
        self.cancel_bulk_requested = False
        
        total = len(phone_numbers)
        sent_count = 0
        failed_count = 0
        results = []

        self.log(f"🚀 Starting bulk campaign for {total} customers (Speed: {speed_delay}s per customer)...")

        for idx, raw_phone in enumerate(phone_numbers, start=1):
            if self.cancel_bulk_requested:
                self.log("🛑 Bulk sending cancelled by user.")
                break

            clean_phone = self.clean_phone_number(raw_phone)
            self.log(f"[{idx}/{total}] Processing customer: +{clean_phone}...")

            # Send to customer
            res = self.send_single(phone=clean_phone, message=message, media_paths=media_paths)
            if res.get("success"):
                sent_count += 1
            else:
                failed_count += 1

            results.append({
                "phone": clean_phone,
                "success": res.get("success"),
                "message": res.get("message")
            })

            # Notify progress
            if progress_callback:
                try:
                    progress_callback({
                        "current": idx,
                        "total": total,
                        "phone": clean_phone,
                        "success": res.get("success"),
                        "sent_count": sent_count,
                        "failed_count": failed_count,
                        "percent": int((idx / total) * 100)
                    })
                except Exception as ex:
                    print(f"Callback error: {ex}")

            # Inter-customer delay with anti-ban human jitter
            if idx < total and not self.cancel_bulk_requested:
                actual_delay = speed_delay
                if speed_delay >= 4.0:
                    import random
                    # Humanized randomized jitter to prevent robotic rate-limiting patterns
                    jitter = random.uniform(0.6, 2.2)
                    actual_delay = round(speed_delay + jitter, 1)
                    
                    # Periodic rest pause every 20 messages to protect account health
                    if idx % 20 == 0:
                        self.log(f"🛡️ Safe Anti-Ban Guard: Resting for 12s after {idx} messages to keep WhatsApp account healthy...")
                        time.sleep(12)
                
                time.sleep(actual_delay)

        self.is_sending = False
        summary = {
            "total": total,
            "processed": len(results),
            "sent": sent_count,
            "failed": failed_count,
            "results": results
        }
        self.log(f"🏁 Campaign finished! Sent: {sent_count}, Failed: {failed_count} of {total}.")
        return summary

    def stop_bulk(self):
        """Cancels an ongoing bulk campaign."""
        self.cancel_bulk_requested = True
        self.log("Stopping bulk sending...")

    def close_session(self):
        """Closes browser session."""
        with self._lock:
            self.is_running = False
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            self.set_status("DISCONNECTED", "Browser closed")
