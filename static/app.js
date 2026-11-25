// State
let attachedFiles = []; // [{original_name, saved_path, type, size_str, url}]
let pollInterval = null;
let currentCustomerMode = 'single'; // 'single' or 'bulk'
let bulkPollingTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  loadAuthUser();
  updatePhonePreview();
  updateMessageCount();
  setupDropzone();
  loadHistory();
  loadChatHistory();
  startStatusPolling();
});

async function loadAuthUser() {
  try {
    const res = await fetch("/api/auth/status");
    const data = await res.json();
    if (data.is_authenticated && data.user) {
      const display = document.getElementById("userMobileDisplay");
      if (display) display.textContent = `+${data.user}`;
    }
  } catch (e) {}
}

// Mode Switching: Single vs Bulk
function switchCustomerMode(mode) {
  currentCustomerMode = mode;
  const tabSingle = document.getElementById("tabSingle");
  const tabBulk = document.getElementById("tabBulk");
  const singleView = document.getElementById("singleModeView");
  const bulkView = document.getElementById("bulkModeView");
  const btnText = document.getElementById("btnSendText");

  if (mode === "single") {
    tabSingle.classList.add("active");
    tabBulk.classList.remove("active");
    singleView.style.display = "block";
    bulkView.style.display = "none";
    btnText.textContent = "⚡ SEND TO SINGLE NUMBER";
  } else {
    tabSingle.classList.remove("active");
    tabBulk.classList.add("active");
    singleView.style.display = "none";
    bulkView.style.display = "block";
    btnText.textContent = "🚀 START BULK SENDING (PHOTOS, VIDEOS, DOCS)";
    updateBulkCount();
  }
}

function updateBulkCount() {
  const numbers = getBulkNumbers();
  const badge = document.getElementById("bulkCountBadge");
  badge.textContent = `${numbers.length} numbers ready`;
  badge.style.background = numbers.length > 0 ? "#10b981" : "#0284c7";
}

function getBulkNumbers() {
  const raw = document.getElementById("bulkNumbersInput").value;
  const items = raw.split(/[\n,;]+/);
  const valid = [];
  items.forEach(item => {
    let clean = item.replace(/\D/g, "");
    if (clean.length >= 7) {
      valid.push(clean);
    }
  });
  return valid;
}

function triggerCsvInput() {
  document.getElementById("csvFileInput").click();
}

function handleCsvImport(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(evt) {
    const text = evt.target.result;
    const lines = text.split(/[\r\n,;]+/);
    const valid = [];
    lines.forEach(l => {
      let clean = l.replace(/\D/g, "");
      if (clean.length >= 7) {
        valid.push(clean);
      }
    });

    if (valid.length > 0) {
      document.getElementById("bulkNumbersInput").value = valid.join("\n");
      updateBulkCount();
      appendLog(`Imported ${valid.length} numbers from ${file.name}.`, "success");
    } else {
      alert("No valid phone numbers found in the imported file.");
    }
  };
  reader.readAsText(file);
}

// Status Polling
function startStatusPolling() {
  checkStatus();
  pollInterval = setInterval(checkStatus, 3000);
}

async function checkStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    
    const badge = document.getElementById("statusBadge");
    const text = document.getElementById("statusText");
    const sessionMsg = document.getElementById("sessionStatusMsg");
    const connectBtn = document.getElementById("btnConnect");

    badge.className = "status-badge";
    const qrBox = document.getElementById("qrBox");
    const qrImg = document.getElementById("qrImage");
    const qrLoading = document.getElementById("qrLoading");

    if (data.status === "CONNECTED") {
      badge.classList.add("status-connected");
      text.textContent = "Connected";
      sessionMsg.textContent = "🟢 WhatsApp Connected and ready to send!";
      sessionMsg.style.color = "#34d399";
      connectBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Connected';
      connectBtn.style.background = "#059669";
      if (qrBox) qrBox.style.display = "none";
    } else if (data.status === "WAITING_FOR_QR") {
      badge.classList.add("status-waiting");
      text.textContent = "Scan QR Code";
      sessionMsg.textContent = "🟡 Please scan the QR code below:";
      sessionMsg.style.color = "#fbbf24";

      // Show QR code right inside Window 1
      if (qrBox) {
        qrBox.style.display = "flex";
        if (data.qr_image) {
          qrImg.src = data.qr_image;
          qrImg.style.display = "block";
          if (qrLoading) qrLoading.style.display = "none";
        } else {
          qrImg.style.display = "none";
          if (qrLoading) qrLoading.style.display = "block";
        }
      }
    } else if (data.status === "STARTING") {
      badge.classList.add("status-waiting");
      text.textContent = "Starting...";
      sessionMsg.textContent = "🟡 Initializing WhatsApp Web browser...";
      sessionMsg.style.color = "#fbbf24";
      if (qrBox) qrBox.style.display = "none";
    } else {
      badge.classList.add("status-disconnected");
      text.textContent = "Disconnected";
      sessionMsg.textContent = "⚪ Click 'Connect WhatsApp' to link session";
      sessionMsg.style.color = "#94a3b8";
      if (qrBox) qrBox.style.display = "none";
    }

    // Refresh logs
    fetchLogs();
  } catch (err) {
    console.error("Status check failed:", err);
  }
}

async function connectWhatsApp() {
  appendLog("Requesting WhatsApp Web session connection...", "info");
  try {
    const res = await fetch("/api/connect", { method: "POST" });
    const data = await res.json();
    appendLog(data.message, "info");
    checkStatus();
  } catch (err) {
    appendLog("Error launching WhatsApp session: " + err, "error");
  }
}

async function manualRefreshQR() {
  appendLog("Refreshing QR code from WhatsApp Web...", "info");
  try {
    const res = await fetch("/api/refresh_qr", { method: "POST" });
    const data = await res.json();
    if (data.qr_image) {
      document.getElementById("qrImage").src = data.qr_image;
      document.getElementById("qrImage").style.display = "block";
      document.getElementById("qrLoading").style.display = "none";
      appendLog("QR code refreshed successfully.", "success");
    } else {
      appendLog("QR code not ready yet, please wait...", "info");
    }
  } catch (e) {
    appendLog("Failed to refresh QR: " + e, "error");
  }
}

async function fetchLogs() {
  try {
    const res = await fetch("/api/logs");
    const data = await res.json();
    if (data.logs && data.logs.length > 0) {
      const consoleBody = document.getElementById("logConsole");
      consoleBody.innerHTML = data.logs.map(l => {
        let cls = "log-line";
        if (l.includes("SUCCESS") || l.includes("sent successfully")) cls += " success";
        else if (l.includes("Error") || l.includes("FAILED") || l.includes("Invalid")) cls += " error";
        else cls += " info";
        return `<div class="${cls}">${escapeHtml(l)}</div>`;
      }).join("");
      consoleBody.scrollTop = consoleBody.scrollHeight;
    }
  } catch (e) {}
}

function clearLogs() {
  document.getElementById("logConsole").innerHTML = "";
}

// Phone Number Preview
function getTargetPhone() {
  const code = document.getElementById("countryCode").value.trim();
  const rawNum = document.getElementById("phoneInput").value.trim();
  let clean = rawNum.replace(/\D/g, "");
  
  if (code && clean.startsWith(code)) {
    return clean;
  } else if (code) {
    if (clean.startsWith("0")) clean = clean.substring(1);
    return code + clean;
  }
  return clean;
}

function updatePhonePreview() {
  const target = getTargetPhone();
  const preview = document.getElementById("phoneTargetPreview");
  if (target && target.length >= 7) {
    preview.textContent = `Target: +${target}`;
    preview.style.color = "#34d399";
  } else {
    preview.textContent = "Target: None";
    preview.style.color = "#64748b";
  }
}

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    const sel = document.getElementById("recentHistory");
    sel.innerHTML = '<option value="">Select from history...</option>';
    if (data.history) {
      data.history.forEach(num => {
        const opt = document.createElement("option");
        opt.value = num;
        opt.textContent = `+${num}`;
        sel.appendChild(opt);
      });
    }
  } catch (e) {}
}

function selectFromHistory() {
  const val = document.getElementById("recentHistory").value;
  if (val) {
    document.getElementById("countryCode").value = "";
    document.getElementById("phoneInput").value = val;
    updatePhonePreview();
  }
}

// Window 2: Formatting & Message Box
function updateMessageCount() {
  const txt = document.getElementById("messageBox").value;
  const chars = txt.length;
  const words = txt.trim() ? txt.trim().split(/\s+/).length : 0;
  document.getElementById("charCount").textContent = `Characters: ${chars} | Words: ${words}`;
}

function wrapText(marker) {
  const box = document.getElementById("messageBox");
  const start = box.selectionStart;
  const end = box.selectionEnd;
  const text = box.value;
  const selected = text.substring(start, end) || "text";
  
  box.value = text.substring(0, start) + `${marker}${selected}${marker}` + text.substring(end);
  box.focus();
  box.setSelectionRange(start + marker.length, start + marker.length + selected.length);
  updateMessageCount();
}

function insertEmoji(emoji) {
  const box = document.getElementById("messageBox");
  const start = box.selectionStart;
  const end = box.selectionEnd;
  const text = box.value;
  
  box.value = text.substring(0, start) + emoji + text.substring(end);
  box.focus();
  box.setSelectionRange(start + emoji.length, start + emoji.length);
  updateMessageCount();
}

function applyTemplate() {
  const val = document.getElementById("templateSelect").value;
  const box = document.getElementById("messageBox");
  const templates = {
    welcome: "Hello! Thank you for connecting with us. How can we assist you today?",
    media: "Hi! Please find attached the photos and videos you requested. Let me know if you need any more details!",
    invoice: "Dear Customer, your order details and invoice have been processed. Please review the attached document.",
    reminder: "Friendly reminder: We have an upcoming scheduled appointment. Looking forward to speaking with you!"
  };
  if (templates[val]) {
    box.value = templates[val];
    updateMessageCount();
  }
}

function clearMessage() {
  document.getElementById("messageBox").value = "";
  updateMessageCount();
}

// Window 3: File Uploads (Photos & Videos)
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  
  ["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFilesToServer(files);
    }
  });
}

function triggerFileInput() {
  document.getElementById("fileInput").click();
}

function triggerPhotoInput() {
  document.getElementById("photoInput").click();
}

function triggerVideoInput() {
  document.getElementById("videoInput").click();
}

function triggerDocInput() {
  document.getElementById("docInput").click();
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files && files.length > 0) {
    uploadFilesToServer(files);
  }
}

async function uploadFilesToServer(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  appendLog(`Uploading ${files.length} file(s) for WhatsApp attachment...`, "info");
  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success && data.files) {
      attachedFiles.push(...data.files);
      renderFilesList();
      appendLog(`Successfully staged ${data.files.length} media file(s).`, "success");
    } else {
      appendLog("Upload error: " + data.message, "error");
    }
  } catch (err) {
    appendLog("File upload failed: " + err, "error");
  }
}

function renderFilesList() {
  const container = document.getElementById("filesList");
  document.getElementById("filesCount").textContent = `Attached: ${attachedFiles.length} file(s)`;

  if (attachedFiles.length === 0) {
    container.innerHTML = `
      <div class="empty-files">
        <i class="fa-regular fa-folder-open"></i>
        <p>No photos or videos attached yet.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = attachedFiles.map((f, idx) => {
    const icon = f.type === "PHOTO" ? "fa-camera" : f.type === "VIDEO" ? "fa-video" : "fa-file";
    const preview = f.type === "PHOTO" 
      ? `<img src="${f.url}" class="file-thumb" alt="thumbnail"/>` 
      : `<i class="fa-solid ${icon}" style="font-size: 20px; color: #38bdf8; width: 32px; text-align: center;"></i>`;

    return `
      <div class="file-item">
        ${preview}
        <div class="file-info">
          <div class="file-name">${escapeHtml(f.original_name)}</div>
          <div class="file-size">${f.type} • ${f.size_str}</div>
        </div>
        <button class="file-del" title="Remove" onclick="removeFile(${idx})">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    `;
  }).join("");
}

function removeFile(index) {
  attachedFiles.splice(index, 1);
  renderFilesList();
}

function clearAllFiles() {
  attachedFiles = [];
  renderFilesList();
}

// Send WhatsApp Execution (Single & Fast Bulk)
async function sendWhatsApp() {
  const message = document.getElementById("messageBox").value.trim();
  const filePaths = attachedFiles.map(f => f.saved_path);

  if (!message && filePaths.length === 0) {
    alert("Please write a message in Window 2 or attach photos, videos, or documents in Window 3.");
    return;
  }

  const sendBtn = document.getElementById("btnSend");
  const sendBtnText = document.getElementById("btnSendText");

  // A. SINGLE CUSTOMER MODE
  if (currentCustomerMode === "single") {
    const phone = getTargetPhone();
    if (!phone || phone.length < 7) {
      alert("Please enter a valid phone number with country code in Window 1.");
      return;
    }

    sendBtn.disabled = true;
    sendBtnText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> SENDING FAST...';
    appendLog(`⚡ Fast sending to +${phone}...`, "info");

    try {
      const res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: phone,
          message: message,
          files: filePaths
        })
      });

      const data = await res.json();
      if (data.success) {
        appendLog("✅ SUCCESS: " + data.message, "success");
        alert("✅ Sent successfully to +" + phone + "!\n\n" + data.message);
        loadHistory();
        loadChatHistory();
      } else {
        appendLog("❌ FAILED: " + data.message, "error");
        alert("❌ Could not send message:\n\n" + data.message);
      }
    } catch (err) {
      appendLog("Error: " + err, "error");
      alert("Server error: " + err);
    } finally {
      sendBtn.disabled = false;
      sendBtnText.textContent = "⚡ SEND TO SINGLE NUMBER";
    }
  }

  // B. BULK NUMBERS MODE (FAST SPEED)
  else {
    const numbers = getBulkNumbers();
    if (numbers.length === 0) {
      alert("Please paste phone numbers or import a CSV/TXT file in Window 1.");
      return;
    }

    const speed = 2.0;
    const progCard = document.getElementById("bulkProgressCard");
    const progBar = document.getElementById("bulkProgressBar");

    progCard.style.display = "flex";
    progBar.style.width = "0%";
    document.getElementById("progCurrent").textContent = "0";
    document.getElementById("progTotal").textContent = numbers.length;
    document.getElementById("progSent").textContent = "0";
    document.getElementById("progFailed").textContent = "0";

    sendBtn.disabled = true;
    sendBtnText.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> RUNNING BULK CAMPAIGN...`;
    appendLog(`🚀 Starting bulk campaign for ${numbers.length} numbers...`, "info");

    try {
      const res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phones: numbers,
          message: message,
          files: filePaths,
          speed: speed,
          is_bulk: true
        })
      });

      const data = await res.json();
      if (data.success) {
        appendLog(data.message || "Campaign launched in background. Monitoring progress...", "info");
        startBulkProgressMonitoring();
      } else {
        appendLog("Bulk campaign failed to start: " + data.message, "error");
        alert("Could not start campaign: " + data.message);
        sendBtn.disabled = false;
        sendBtnText.textContent = "🚀 START BULK SENDING (PHOTOS, VIDEOS, DOCS)";
        progCard.style.display = "none";
      }
    } catch (err) {
      appendLog("Bulk launch error: " + err, "error");
      sendBtn.disabled = false;
      sendBtnText.textContent = "🚀 START BULK SENDING (PHOTOS, VIDEOS, DOCS)";
      progCard.style.display = "none";
    }
  }
}

function startBulkProgressMonitoring() {
  if (bulkPollingTimer) clearInterval(bulkPollingTimer);

  bulkPollingTimer = setInterval(async () => {
    try {
      const res = await fetch("/api/bulk_status");
      const st = await res.json();

      document.getElementById("progCurrent").textContent = st.current;
      document.getElementById("progTotal").textContent = st.total;
      document.getElementById("progSent").textContent = st.sent;
      document.getElementById("progFailed").textContent = st.failed;
      document.getElementById("progLastCustomer").textContent = st.last_phone ? `+${st.last_phone} (${st.last_status})` : "-";
      document.getElementById("bulkProgressBar").style.width = `${st.percent}%`;

      if (!st.is_running && st.total > 0 && st.current >= st.total) {
        clearInterval(bulkPollingTimer);
        const sendBtn = document.getElementById("btnSend");
        const sendBtnText = document.getElementById("btnSendText");
        sendBtn.disabled = false;
        sendBtnText.textContent = "🚀 START BULK SENDING (PHOTOS, VIDEOS, DOCS)";
        appendLog(`🏁 Bulk campaign completed! Sent: ${st.sent}, Failed: ${st.failed} of ${st.total}.`, "success");
        loadChatHistory();
        alert(`🏁 Campaign Finished!\n\nTotal: ${st.total}\nSent: ${st.sent}\nFailed: ${st.failed}`);
      }
    } catch (e) {}
  }, 1000);
}

async function stopBulkCampaign() {
  appendLog("Stopping bulk campaign...", "info");
  try {
    await fetch("/api/stop_bulk", { method: "POST" });
    if (bulkPollingTimer) clearInterval(bulkPollingTimer);
    document.getElementById("btnSend").disabled = false;
    document.getElementById("btnSendText").textContent = "🚀 START BULK SENDING (PHOTOS, VIDEOS, DOCS)";
    document.getElementById("bulkProgressCard").style.display = "none";
    appendLog("Bulk campaign was stopped by user.", "info");
  } catch (e) {}
}

// Helpers
function appendLog(text, type = "info") {
  const consoleBody = document.getElementById("logConsole");
  if (!consoleBody) {
    console.log(`[${type}] ${text}`);
    return;
  }
  const time = new Date().toTimeString().split(' ')[0];
  const div = document.createElement("div");
  div.className = `log-line ${type}`;
  div.textContent = `[${time}] ${text}`;
  consoleBody.appendChild(div);
  consoleBody.scrollTop = consoleBody.scrollHeight;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// --- CHAT HISTORY (SAVED MESSAGES) ---
let cachedChatHistory = [];

async function loadChatHistory() {
  try {
    const res = await fetch("/api/chat_history");
    const data = await res.json();
    cachedChatHistory = data.history || [];
    renderChatHistory(cachedChatHistory);
  } catch (e) {
    console.error("Error loading chat history:", e);
  }
}

function renderChatHistory(history) {
  const tbody = document.getElementById("chatHistoryTableBody");
  const badge = document.getElementById("chatHistoryCountBadge");
  if (!tbody) return;

  if (badge) {
    badge.textContent = `${history.length} sent`;
  }

  if (!history || history.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-history-row">
        <td colspan="5">
          <i class="fa-regular fa-comments"></i>
          <span>No chat history yet. Sent messages will be automatically saved and displayed here.</span>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = history.map(item => {
    const isSent = item.status === "SENT";
    const statusBadge = isSent 
      ? '<span class="badge-status-sent"><i class="fa-solid fa-check"></i> Sent</span>'
      : '<span class="badge-status-failed"><i class="fa-solid fa-xmark"></i> Failed</span>';

    const mediaDisplay = item.files_count > 0 
      ? `<span title="${escapeHtml(item.files_names?.join(', ') || '')}"><i class="fa-solid fa-paperclip text-green"></i> ${item.files_count} file(s)</span>`
      : '<span class="text-dim">-</span>';

    return `
      <tr>
        <td style="color: var(--text-muted); font-size: 12px; white-space: nowrap;">
          <div><b>${escapeHtml(item.time_display || '')}</b></div>
          <small class="text-dim">${escapeHtml(item.date_display || '')}</small>
        </td>
        <td style="font-weight: 600; white-space: nowrap;">
          <i class="fa-brands fa-whatsapp text-green" style="margin-right: 4px;"></i>+${escapeHtml(item.phone)}
        </td>
        <td style="max-width: 380px; word-break: break-word;" title="${escapeHtml(item.full_message || '')}">
          ${escapeHtml(item.message || '(No text)')}
        </td>
        <td style="white-space: nowrap;">
          ${mediaDisplay}
        </td>
        <td>
          ${statusBadge}
        </td>
      </tr>
    `;
  }).join("");
}

async function clearChatHistory() {
  if (!confirm("Are you sure you want to clear your saved chat history?")) return;
  try {
    await fetch("/api/clear_chat_history", { method: "POST" });
    cachedChatHistory = [];
    renderChatHistory([]);
  } catch (e) {
    alert("Error clearing history: " + e);
  }
}

function exportChatHistoryCsv() {
  if (!cachedChatHistory || cachedChatHistory.length === 0) {
    alert("No chat history to export yet.");
    return;
  }

  const headers = ["Timestamp", "Recipient Phone", "Message", "Files Count", "Files Attached", "Status", "Error"];
  const rows = cachedChatHistory.map(r => [
    `"${r.timestamp || ''}"`,
    `"+${r.phone || ''}"`,
    `"${(r.full_message || r.message || '').replace(/"/g, '""')}"`,
    r.files_count || 0,
    `"${(r.files_names || []).join('; ')}"`,
    `"${r.status || ''}"`,
    `"${(r.error || '').replace(/"/g, '""')}"`
  ]);

  const csvContent = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `aadhya_chat_history_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
