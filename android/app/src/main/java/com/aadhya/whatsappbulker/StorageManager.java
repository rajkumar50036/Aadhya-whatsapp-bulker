package com.aadhya.whatsappbulker;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class StorageManager {

    private static final String HISTORY_FILE = "history.json";
    private static final String TEMPLATES_FILE = "templates.json";

    public static List<HistoryItem> loadHistory(Context context) {
        List<HistoryItem> list = new ArrayList<>();
        File file = new File(context.getFilesDir(), HISTORY_FILE);
        if (!file.exists()) return list;

        try (FileInputStream fis = new FileInputStream(file)) {
            byte[] buffer = new byte[(int) file.length()];
            fis.read(buffer);
            String json = new String(buffer, StandardCharsets.UTF_8);
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                list.add(HistoryItem.fromJSONObject(arr.getJSONObject(i)));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return list;
    }

    public static void saveHistory(Context context, List<HistoryItem> list) {
        File file = new File(context.getFilesDir(), HISTORY_FILE);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            JSONArray arr = new JSONArray();
            for (HistoryItem item : list) {
                arr.put(item.toJSONObject());
            }
            fos.write(arr.toString(2).getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void addHistoryItem(Context context, HistoryItem item) {
        List<HistoryItem> list = loadHistory(context);
        list.add(0, item); // Latest first
        // Limit to 200 items
        if (list.size() > 200) {
            list = list.subList(0, 200);
        }
        saveHistory(context, list);
    }

    public static void clearHistory(Context context) {
        File file = new File(context.getFilesDir(), HISTORY_FILE);
        if (file.exists()) file.delete();
    }

    public static String exportHistoryCSV(Context context) {
        List<HistoryItem> list = loadHistory(context);
        StringBuilder sb = new StringBuilder();
        sb.append("Timestamp,Recipient,Message,Media Attached,Status\n");
        for (HistoryItem item : list) {
            sb.append("\"").append(item.getTimestamp()).append("\",");
            sb.append("\"+").append(item.getPhone()).append("\",");
            sb.append("\"").append(item.getMessage().replace("\"", "\"\"").replace("\n", " ")).append("\",");
            sb.append("\"").append(item.getMediaName()).append("\",");
            sb.append("\"").append(item.getStatus()).append("\"\n");
        }
        return sb.toString();
    }

    public static List<TemplateItem> loadTemplates(Context context) {
        List<TemplateItem> list = new ArrayList<>();
        File file = new File(context.getFilesDir(), TEMPLATES_FILE);
        if (!file.exists()) {
            // Default built-in templates
            list.add(new TemplateItem("Welcome Greeting", "Hello! 👋 Thank you for connecting with us. How can we assist you today?"));
            list.add(new TemplateItem("Photo / Video Share", "Hi! 📸 Please find attached the photos and updates you requested. Let me know if you need any more details!"));
            list.add(new TemplateItem("Invoice / Order Update", "Dear Customer, 🧾 your order details and invoice have been processed. Please review!"));
            list.add(new TemplateItem("Appointment Reminder", "Friendly reminder: 📅 We have an upcoming scheduled appointment. Looking forward to speaking with you!"));
            list.add(new TemplateItem("Special Offer / Discount", "Exclusive Offer! 🚀 Get a special 20% discount on all our services this week. Reply YES to claim!"));
            saveTemplates(context, list);
            return list;
        }

        try (FileInputStream fis = new FileInputStream(file)) {
            byte[] buffer = new byte[(int) file.length()];
            fis.read(buffer);
            String json = new String(buffer, StandardCharsets.UTF_8);
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                list.add(TemplateItem.fromJSONObject(arr.getJSONObject(i)));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return list;
    }

    public static void saveTemplates(Context context, List<TemplateItem> list) {
        File file = new File(context.getFilesDir(), TEMPLATES_FILE);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            JSONArray arr = new JSONArray();
            for (TemplateItem item : list) {
                arr.put(item.toJSONObject());
            }
            fos.write(arr.toString(2).getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
