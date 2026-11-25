package com.aadhya.whatsappbulker;

import org.json.JSONException;
import org.json.JSONObject;

public class TemplateItem {
    private String title;
    private String content;

    public TemplateItem(String title, String content) {
        this.title = title;
        this.content = content;
    }

    public String getTitle() { return title; }
    public String getContent() { return content; }

    public JSONObject toJSONObject() throws JSONException {
        JSONObject obj = new JSONObject();
        obj.put("title", title);
        obj.put("content", content);
        return obj;
    }

    public static TemplateItem fromJSONObject(JSONObject obj) {
        return new TemplateItem(obj.optString("title", ""), obj.optString("content", ""));
    }
}
