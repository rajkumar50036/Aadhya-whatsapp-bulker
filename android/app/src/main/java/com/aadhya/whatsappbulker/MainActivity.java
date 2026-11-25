package com.aadhya.whatsappbulker;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.net.URLEncoder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    // Tab Buttons
    private Button tabSender, tabHistory, tabTemplates, tabAntiBan;
    private View viewSender, viewHistory, viewTemplates, viewAntiBan;

    // Accessibility Banner
    private View cardAccessibilityBanner;
    private TextView badgeServiceStatus;
    private Button btnEnableAccessibility;

    // Section 1: Phone Numbers
    private Button btnModeSingle, btnModeBulk;
    private TextView txtCountBadge, btnClearNumbers;
    private EditText editPhoneNumbers;
    private boolean isSingleMode = false;

    // Section 2: Message Composer
    private TextView txtCharCount, btnFormatBold, btnFormatItalic, btnFormatStrike, btnInsertName;
    private EditText editMessage;
    private LinearLayout layoutEmojis;

    // Section 3: Attach Media
    private Button btnPickMedia;
    private View layoutAttachedMedia;
    private TextView txtAttachedMediaName, btnRemoveMedia;
    private Uri attachedMediaUri = null;
    private String attachedMediaName = "";

    // Section 4: Campaign Launcher
    private Button btnStartBulkCampaign;
    private TextView txtLiveCampaignProgress;

    // Section 5: History View
    private RecyclerView recyclerHistory;
    private HistoryAdapter historyAdapter;
    private List<HistoryItem> historyList = new ArrayList<>();
    private TextView txtHistoryTitle;
    private Button btnExportCSV, btnClearHistory;

    // Section 6: Templates View
    private LinearLayout layoutTemplatesList;

    // Section 7: Anti-Ban View
    private SeekBar seekAntiBanDelay;
    private TextView txtAntiBanDelayValue;
    private int delaySeconds = 3;

    // Campaign State
    private boolean isSending = false;
    private int currentIndex = 0;
    private List<String> numbersList = new ArrayList<>();
    private final Handler handler = new Handler(Looper.getMainLooper());

    // Media Picker Launcher
    private final ActivityResultLauncher<String> mediaPickerLauncher =
        registerForActivityResult(new ActivityResultContracts.GetContent(), uri -> {
            if (uri != null) {
                attachedMediaUri = uri;
                attachedMediaName = getFileNameFromUri(uri);
                txtAttachedMediaName.setText(attachedMediaName);
                layoutAttachedMedia.setVisibility(View.VISIBLE);
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        bindViews();
        setupTabs();
        setupSection1Numbers();
        setupSection2Composer();
        setupSection3Media();
        setupSection4Campaign();
        setupSection5History();
        setupSection6Templates();
        setupSection7AntiBan();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateAccessibilityStatus();
        loadHistoryData();
    }

    private void bindViews() {
        tabSender = findViewById(R.id.tabSender);
        tabHistory = findViewById(R.id.tabHistory);
        tabTemplates = findViewById(R.id.tabTemplates);
        tabAntiBan = findViewById(R.id.tabAntiBan);

        viewSender = findViewById(R.id.viewSender);
        viewHistory = findViewById(R.id.viewHistory);
        viewTemplates = findViewById(R.id.viewTemplates);
        viewAntiBan = findViewById(R.id.viewAntiBan);

        cardAccessibilityBanner = findViewById(R.id.cardAccessibilityBanner);
        badgeServiceStatus = findViewById(R.id.badgeServiceStatus);
        btnEnableAccessibility = findViewById(R.id.btnEnableAccessibility);

        btnModeSingle = findViewById(R.id.btnModeSingle);
        btnModeBulk = findViewById(R.id.btnModeBulk);
        txtCountBadge = findViewById(R.id.txtCountBadge);
        btnClearNumbers = findViewById(R.id.btnClearNumbers);
        editPhoneNumbers = findViewById(R.id.editPhoneNumbers);

        txtCharCount = findViewById(R.id.txtCharCount);
        btnFormatBold = findViewById(R.id.btnFormatBold);
        btnFormatItalic = findViewById(R.id.btnFormatItalic);
        btnFormatStrike = findViewById(R.id.btnFormatStrike);
        btnInsertName = findViewById(R.id.btnInsertName);
        editMessage = findViewById(R.id.editMessage);
        layoutEmojis = findViewById(R.id.layoutEmojis);

        btnPickMedia = findViewById(R.id.btnPickMedia);
        layoutAttachedMedia = findViewById(R.id.layoutAttachedMedia);
        txtAttachedMediaName = findViewById(R.id.txtAttachedMediaName);
        btnRemoveMedia = findViewById(R.id.btnRemoveMedia);

        btnStartBulkCampaign = findViewById(R.id.btnStartBulkCampaign);
        txtLiveCampaignProgress = findViewById(R.id.txtLiveCampaignProgress);

        recyclerHistory = findViewById(R.id.recyclerHistory);
        txtHistoryTitle = findViewById(R.id.txtHistoryTitle);
        btnExportCSV = findViewById(R.id.btnExportCSV);
        btnClearHistory = findViewById(R.id.btnClearHistory);

        layoutTemplatesList = findViewById(R.id.layoutTemplatesList);

        seekAntiBanDelay = findViewById(R.id.seekAntiBanDelay);
        txtAntiBanDelayValue = findViewById(R.id.txtAntiBanDelayValue);
    }

    // ==================== TABS SETUP ====================
    private void setupTabs() {
        tabSender.setOnClickListener(v -> switchTab(0));
        tabHistory.setOnClickListener(v -> switchTab(1));
        tabTemplates.setOnClickListener(v -> switchTab(2));
        tabAntiBan.setOnClickListener(v -> switchTab(3));

        btnEnableAccessibility.setOnClickListener(v -> {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
            Toast.makeText(this, "Enable 'Aadhya WhatsApp Bulker' in Accessibility", Toast.LENGTH_LONG).show();
        });
    }

    private void switchTab(int index) {
        viewSender.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
        viewHistory.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
        viewTemplates.setVisibility(index == 2 ? View.VISIBLE : View.GONE);
        viewAntiBan.setVisibility(index == 3 ? View.VISIBLE : View.GONE);

        int activeBg = ContextCompat.getColor(this, R.color.primary);
        int inactiveBg = ContextCompat.getColor(this, R.color.card_bg);
        int activeText = ContextCompat.getColor(this, R.color.bg_dark);
        int inactiveText = ContextCompat.getColor(this, R.color.text_white);

        tabSender.setBackgroundColor(index == 0 ? activeBg : inactiveBg);
        tabSender.setTextColor(index == 0 ? activeText : inactiveText);

        tabHistory.setBackgroundColor(index == 1 ? activeBg : inactiveBg);
        tabHistory.setTextColor(index == 1 ? activeText : inactiveText);

        tabTemplates.setBackgroundColor(index == 2 ? activeBg : inactiveBg);
        tabTemplates.setTextColor(index == 2 ? activeText : inactiveText);

        tabAntiBan.setBackgroundColor(index == 3 ? activeBg : inactiveBg);
        tabAntiBan.setTextColor(index == 3 ? activeText : inactiveText);

        if (index == 1) loadHistoryData();
        if (index == 2) loadTemplatesData();
    }

    private void updateAccessibilityStatus() {
        if (WhatsAppAccessibilityService.isServiceRunning) {
            badgeServiceStatus.setText("⚡ Auto-Send ON");
            cardAccessibilityBanner.setVisibility(View.GONE);
        } else {
            badgeServiceStatus.setText("⚡ Auto-Send OFF");
            cardAccessibilityBanner.setVisibility(View.VISIBLE);
        }
    }

    // ==================== SECTION 1: NUMBERS ====================
    private void setupSection1Numbers() {
        btnModeSingle.setOnClickListener(v -> {
            isSingleMode = true;
            btnModeSingle.setBackgroundColor(ContextCompat.getColor(this, R.color.primary));
            btnModeSingle.setTextColor(ContextCompat.getColor(this, R.color.bg_dark));
            btnModeBulk.setBackgroundColor(ContextCompat.getColor(this, R.color.card_bg));
            btnModeBulk.setTextColor(ContextCompat.getColor(this, R.color.text_white));
            editPhoneNumbers.setHint("Enter 1 phone number with country code:\n919876543210");
            btnStartBulkCampaign.setText("⚡ SEND TO SINGLE NUMBER");
            parseNumbers();
        });

        btnModeBulk.setOnClickListener(v -> {
            isSingleMode = false;
            btnModeBulk.setBackgroundColor(ContextCompat.getColor(this, R.color.primary));
            btnModeBulk.setTextColor(ContextCompat.getColor(this, R.color.bg_dark));
            btnModeSingle.setBackgroundColor(ContextCompat.getColor(this, R.color.card_bg));
            btnModeSingle.setTextColor(ContextCompat.getColor(this, R.color.text_white));
            editPhoneNumbers.setHint("Type or paste numbers with country code:\n919876543210\n919876543211\n(One number per line or separated by commas)");
            btnStartBulkCampaign.setText("🚀 START BULK SENDING");
            parseNumbers();
        });

        editPhoneNumbers.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { parseNumbers(); }
            @Override public void afterTextChanged(Editable s) {}
        });

        btnClearNumbers.setOnClickListener(v -> {
            editPhoneNumbers.setText("");
            parseNumbers();
        });
    }

    private void parseNumbers() {
        String raw = editPhoneNumbers.getText().toString().trim();
        numbersList.clear();
        if (!raw.isEmpty()) {
            String[] tokens = raw.split("[,\\n\\r]+");
            for (String t : tokens) {
                String clean = t.replaceAll("[^0-9]", "");
                if (clean.length() >= 7) {
                    numbersList.add(clean);
                    if (isSingleMode) break; // Only take first number in single mode
                }
            }
        }
        txtCountBadge.setText(numbersList.size() + (isSingleMode ? " Number" : " Numbers"));
    }

    // ==================== SECTION 2: COMPOSER ====================
    private void setupSection2Composer() {
        // Build Quick Emoji Bar
        String[] emojis = {"😊", "👋", "🙏", "🚀", "⚡", "🎉", "🔥", "📞", "💬", "💯", "✅", "👍", "❤️", "🎯", "🧾"};
        for (String emoji : emojis) {
            TextView tv = new TextView(this);
            tv.setText(emoji);
            tv.setTextSize(18);
            tv.setPadding(12, 4, 12, 4);
            tv.setOnClickListener(v -> insertTextAtCursor(emoji));
            layoutEmojis.addView(tv);
        }

        // Formatting buttons
        btnFormatBold.setOnClickListener(v -> wrapSelectionOrInsert("*", "*", "bold text"));
        btnFormatItalic.setOnClickListener(v -> wrapSelectionOrInsert("_", "_", "italic text"));
        btnFormatStrike.setOnClickListener(v -> wrapSelectionOrInsert("~", "~", "strikethrough text"));
        btnInsertName.setOnClickListener(v -> insertTextAtCursor("{name}"));

        editMessage.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                txtCharCount.setText(s.length() + " chars");
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void insertTextAtCursor(String text) {
        int start = Math.max(editMessage.getSelectionStart(), 0);
        int end = Math.max(editMessage.getSelectionEnd(), 0);
        editMessage.getText().replace(Math.min(start, end), Math.max(start, end), text, 0, text.length());
    }

    private void wrapSelectionOrInsert(String prefix, String suffix, String placeholder) {
        int start = editMessage.getSelectionStart();
        int end = editMessage.getSelectionEnd();
        if (start < 0 || end < 0 || start == end) {
            insertTextAtCursor(prefix + placeholder + suffix);
        } else {
            String selected = editMessage.getText().subSequence(start, end).toString();
            editMessage.getText().replace(start, end, prefix + selected + suffix);
        }
    }

    // ==================== SECTION 3: MEDIA ====================
    private void setupSection3Media() {
        btnPickMedia.setOnClickListener(v -> mediaPickerLauncher.launch("image/*,video/*"));
        btnRemoveMedia.setOnClickListener(v -> {
            attachedMediaUri = null;
            attachedMediaName = "";
            layoutAttachedMedia.setVisibility(View.GONE);
        });
    }

    private String getFileNameFromUri(Uri uri) {
        String result = "media_file";
        if (uri.getScheme().equals("content")) {
            try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
                if (cursor != null && cursor.moveToFirst()) {
                    int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                    if (index >= 0) result = cursor.getString(index);
                }
            } catch (Exception e) {}
        }
        return result;
    }

    // ==================== SECTION 4: CAMPAIGN LAUNCHER ====================
    private void setupSection4Campaign() {
        btnStartBulkCampaign.setOnClickListener(v -> {
            if (isSending) {
                stopCampaign();
            } else {
                startCampaign();
            }
        });
    }

    private void startCampaign() {
        parseNumbers();
        String message = editMessage.getText().toString().trim();

        if (numbersList.isEmpty()) {
            Toast.makeText(this, "Please enter at least one valid phone number", Toast.LENGTH_SHORT).show();
            return;
        }

        if (message.isEmpty() && attachedMediaUri == null) {
            Toast.makeText(this, "Please compose a message or attach a file", Toast.LENGTH_SHORT).show();
            return;
        }

        isSending = true;
        currentIndex = 0;
        btnStartBulkCampaign.setText("⏹ STOP CAMPAIGN");
        btnStartBulkCampaign.setBackgroundColor(ContextCompat.getColor(this, R.color.border_color));
        WhatsAppAccessibilityService.isAutoSendEnabled = true;

        sendNextContact();
    }

    private void stopCampaign() {
        isSending = false;
        btnStartBulkCampaign.setText(isSingleMode ? "⚡ SEND TO SINGLE NUMBER" : "🚀 START BULK SENDING");
        btnStartBulkCampaign.setBackgroundColor(ContextCompat.getColor(this, R.color.primary));
        WhatsAppAccessibilityService.isAutoSendEnabled = false;
        txtLiveCampaignProgress.setText("Campaign stopped.");
    }

    private void sendNextContact() {
        if (!isSending) return;

        if (currentIndex >= numbersList.size()) {
            stopCampaign();
            txtLiveCampaignProgress.setText("🎉 Completed! Sent to " + numbersList.size() + " contacts.");
            Toast.makeText(this, "Bulk sending completed successfully!", Toast.LENGTH_LONG).show();
            return;
        }

        String phone = numbersList.get(currentIndex);
        String message = editMessage.getText().toString();
        txtLiveCampaignProgress.setText("Sending " + (currentIndex + 1) + " of " + numbersList.size() + " to +" + phone + "...");

        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            if (attachedMediaUri != null) {
                intent = new Intent(Intent.ACTION_SEND);
                intent.putExtra(Intent.EXTRA_STREAM, attachedMediaUri);
                intent.putExtra(Intent.EXTRA_TEXT, message);
                intent.setType(getContentResolver().getType(attachedMediaUri));
                intent.putExtra("jid", phone + "@s.whatsapp.net");
            } else {
                String url = "https://api.whatsapp.com/send?phone=" + phone + "&text=" + URLEncoder.encode(message, "UTF-8");
                intent.setData(Uri.parse(url));
            }

            intent.setPackage("com.whatsapp");
            if (intent.resolveActivity(getPackageManager()) == null) {
                intent.setPackage("com.whatsapp.w4b");
            }
            if (intent.resolveActivity(getPackageManager()) == null) {
                intent.setPackage(null);
            }

            startActivity(intent);

            // Record to persistent Chat History
            String timeStamp = new SimpleDateFormat("dd-MM-yyyy HH:mm:ss", Locale.getDefault()).format(new Date());
            StorageManager.addHistoryItem(this, new HistoryItem(
                String.valueOf(System.currentTimeMillis()),
                timeStamp,
                phone,
                message.isEmpty() ? "[Attachment]" : message,
                attachedMediaName,
                "Sent"
            ));

            currentIndex++;
            handler.postDelayed(this::sendNextContact, delaySeconds * 1000L);

        } catch (Exception e) {
            Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            currentIndex++;
            handler.postDelayed(this::sendNextContact, 2000);
        }
    }

    // ==================== SECTION 5: HISTORY ====================
    private void setupSection5History() {
        recyclerHistory.setLayoutManager(new LinearLayoutManager(this));
        loadHistoryData();

        btnClearHistory.setOnClickListener(v -> {
            StorageManager.clearHistory(this);
            loadHistoryData();
            Toast.makeText(this, "Chat History Cleared", Toast.LENGTH_SHORT).show();
        });

        btnExportCSV.setOnClickListener(v -> {
            String csv = StorageManager.exportHistoryCSV(this);
            Intent shareIntent = new Intent(Intent.ACTION_SEND);
            shareIntent.setType("text/plain");
            shareIntent.putExtra(Intent.EXTRA_SUBJECT, "Aadhya WhatsApp Bulker - Chat History");
            shareIntent.putExtra(Intent.EXTRA_TEXT, csv);
            startActivity(Intent.createChooser(shareIntent, "Export Chat History CSV"));
        });
    }

    private void loadHistoryData() {
        historyList = StorageManager.loadHistory(this);
        txtHistoryTitle.setText("Chat History (" + historyList.size() + ")");
        historyAdapter = new HistoryAdapter(historyList);
        recyclerHistory.setAdapter(historyAdapter);
    }

    // ==================== SECTION 6: TEMPLATES ====================
    private void setupSection6Templates() {
        loadTemplatesData();
    }

    private void loadTemplatesData() {
        layoutTemplatesList.removeAllViews();
        List<TemplateItem> templates = StorageManager.loadTemplates(this);

        for (TemplateItem t : templates) {
            View card = getLayoutInflater().inflate(R.layout.item_history, layoutTemplatesList, false);
            TextView txtTitle = card.findViewById(R.id.txtItemPhone);
            TextView txtContent = card.findViewById(R.id.txtItemMessage);
            TextView txtAction = card.findViewById(R.id.txtItemStatus);
            TextView txtTime = card.findViewById(R.id.txtItemTime);

            txtTitle.setText(t.getTitle());
            txtContent.setText(t.getContent());
            txtAction.setText("Use Template");
            txtTime.setVisibility(View.GONE);

            card.setOnClickListener(v -> {
                editMessage.setText(t.getContent());
                switchTab(0); // Switch to Sender Tab
                Toast.makeText(this, "Loaded: " + t.getTitle(), Toast.LENGTH_SHORT).show();
            });

            layoutTemplatesList.addView(card);
        }
    }

    // ==================== SECTION 7: ANTI-BAN ====================
    private void setupSection7AntiBan() {
        seekAntiBanDelay.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                delaySeconds = Math.max(1, progress);
                txtAntiBanDelayValue.setText(delaySeconds + " seconds");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {}
        });
    }
}
