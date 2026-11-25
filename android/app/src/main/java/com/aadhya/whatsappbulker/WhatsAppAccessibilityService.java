package com.aadhya.whatsappbulker;

import android.accessibilityservice.AccessibilityService;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class WhatsAppAccessibilityService extends AccessibilityService {

    public static boolean isServiceRunning = false;
    public static boolean isAutoSendEnabled = false;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        isServiceRunning = true;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (!isAutoSendEnabled) return;

        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;

        // Try finding WhatsApp Send button by ID: com.whatsapp:id/send
        List<AccessibilityNodeInfo> sendNodes = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/send");
        if (sendNodes.isEmpty()) {
            sendNodes = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp.w4b:id/send");
        }

        // Try finding by ContentDescription
        if (sendNodes.isEmpty()) {
            sendNodes = rootNode.findAccessibilityNodeInfosByText("Send");
        }

        if (!sendNodes.isEmpty()) {
            for (AccessibilityNodeInfo node : sendNodes) {
                if (node.isClickable() || node.isEnabled()) {
                    node.performAction(AccessibilityNodeInfo.ACTION_CLICK);

                    // Delay 1.5s then press Back to return to Aadhya WhatsApp Bulker
                    handler.postDelayed(() -> {
                        performGlobalAction(GLOBAL_ACTION_BACK);
                    }, 1500);
                    break;
                }
            }
        }
    }

    @Override
    public void onInterrupt() {
        isServiceRunning = false;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isServiceRunning = false;
    }
}
