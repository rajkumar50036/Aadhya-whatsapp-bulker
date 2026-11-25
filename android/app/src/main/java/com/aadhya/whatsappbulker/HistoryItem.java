package com.aadhya.whatsappbulker;

import org.json.JSONException;
import org.json.JSONObject;

public class HistoryItem {
    private String id;
    private String timestamp;
    private String phone;
    private String message;
    private String mediaName;
    private String status; // "Sent", "Failed", "Pending"

    public HistoryItem(String id, String timestamp, String phone, String message, String mediaName, String status) {
        this.id = id;
        this.timestamp = timestamp;
        this.phone = phone;
        this.message = message;
        this.mediaName = mediaName != null ? mediaName : "";
        this.status = status;
    }

    public String getId() { return id; }
    public String getTimestamp() { return timestamp; }
    public String getPhone() { return phone; }
    public String getMessage() { return message; }
    public String getMediaName() { return mediaName; }
    public String getStatus() { return status; }

    public JSONObject toJSONObject() throws JSONException {
        JSONObject obj = new JSONObject();
        obj.put("id", id);
        obj.put("timestamp", timestamp);
        obj.put("phone", phone);
        obj.put("message", message);
        obj.put("media_name", mediaName);
        obj.put("status", status);
        return obj;
    }

    public static HistoryItem fromJSONObject(JSONObject obj) {
        return new HistoryItem(
            obj.optString("id", String.valueOf(System.currentTimeMillis())),
            obj.optString("timestamp", ""),
            obj.optString("phone", ""),
            obj.optString("message", ""),
            obj.optString("media_name", ""),
            obj.optString("status", "Sent")
        );
    }
}
