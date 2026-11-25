package com.aadhya.whatsappbulker;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.Editable;
import android.text.TextWatcher;
import android.widget.Button;
import android.widget.EditText;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private EditText inputPhoneNumbers, inputMessage;
    private TextView txtNumberCount, txtDelayDisplay, txtProgress, txtServiceStatus;
    private SeekBar seekDelay;
    private Button btnStartBulk, btnEnableService;

    private int delaySeconds = 3;
    private boolean isSending = false;
    private int currentIndex = 0;
    private List<String> numbersList = new ArrayList<>();
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        inputPhoneNumbers = findViewById(R.id.inputPhoneNumbers);
        inputMessage = findViewById(R.id.inputMessage);
        txtNumberCount = findViewById(R.id.txtNumberCount);
        txtDelayDisplay = findViewById(R.id.txtDelayDisplay);
        txtProgress = findViewById(R.id.txtProgress);
        txtServiceStatus = findViewById(R.id.txtServiceStatus);
        seekDelay = findViewById(R.id.seekDelay);
        btnStartBulk = findViewById(R.id.btnStartBulk);
        btnEnableService = findViewById(R.id.btnEnableService);

        setupListeners();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateServiceStatus();
    }

    private void updateServiceStatus() {
        if (WhatsAppAccessibilityService.isServiceRunning) {
            txtServiceStatus.setText("⚡ Auto-Send Service: Active & Running");
            btnEnableService.setText("Auto-Send Active ✓");
            btnEnableService.setEnabled(false);
        } else {
            txtServiceStatus.setText("⚡ Auto-Send Service: Disabled");
            btnEnableService.setText("Enable Auto-Send in Settings");
            btnEnableService.setEnabled(true);
        }
    }

    private void setupListeners() {
        btnEnableService.setOnClickListener(v -> {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
            Toast.makeText(this, "Enable 'Aadhya WhatsApp Bulker' in Accessibility", Toast.LENGTH_LONG).show();
        });

        seekDelay.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                delaySeconds = Math.max(1, progress);
                txtDelayDisplay.setText(delaySeconds + " seconds");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {}
        });

        inputPhoneNumbers.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                parseNumbers();
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        btnStartBulk.setOnClickListener(v -> {
            if (isSending) {
                stopSending();
            } else {
                startSending();
            }
        });
    }

    private void parseNumbers() {
        String raw = inputPhoneNumbers.getText().toString().trim();
        numbersList.clear();
        if (!raw.isEmpty()) {
            String[] tokens = raw.split("[,\\n\\r]+");
            for (String t : tokens) {
                String clean = t.replaceAll("[^0-9]", "");
                if (clean.length() >= 7) {
                    numbersList.add(clean);
                }
            }
        }
        txtNumberCount.setText(numbersList.size() + " Numbers");
    }

    private void startSending() {
        parseNumbers();
        String message = inputMessage.getText().toString().trim();

        if (numbersList.isEmpty()) {
            Toast.makeText(this, "Please enter at least one phone number", Toast.LENGTH_SHORT).show();
            return;
        }

        if (message.isEmpty()) {
            Toast.makeText(this, "Please enter a message to send", Toast.LENGTH_SHORT).show();
            return;
        }

        isSending = true;
        currentIndex = 0;
        btnStartBulk.setText("⏹ STOP CAMPAIGN");
        WhatsAppAccessibilityService.isAutoSendEnabled = true;

        sendNextNumber();
    }

    private void stopSending() {
        isSending = false;
        btnStartBulk.setText("🚀 START BULK SENDING");
        WhatsAppAccessibilityService.isAutoSendEnabled = false;
        txtProgress.setText("Campaign stopped.");
    }

    private void sendNextNumber() {
        if (!isSending) return;

        if (currentIndex >= numbersList.size()) {
            stopSending();
            txtProgress.setText("🎉 Completed! Sent to " + numbersList.size() + " contacts.");
            Toast.makeText(this, "Bulk sending completed successfully!", Toast.LENGTH_LONG).show();
            return;
        }

        String phone = numbersList.get(currentIndex);
        String message = inputMessage.getText().toString();
        txtProgress.setText("Sending " + (currentIndex + 1) + " of " + numbersList.size() + " to +" + phone + "...");

        try {
            String url = "https://api.whatsapp.com/send?phone=" + phone + "&text=" + URLEncoder.encode(message, "UTF-8");
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setData(Uri.parse(url));
            intent.setPackage("com.whatsapp");

            // Fallback to WhatsApp Business if regular WhatsApp not found
            if (intent.resolveActivity(getPackageManager()) == null) {
                intent.setPackage("com.whatsapp.w4b");
            }
            if (intent.resolveActivity(getPackageManager()) == null) {
                intent.setPackage(null); // System default
            }

            startActivity(intent);

            currentIndex++;
            // Schedule next message after chosen delay
            handler.postDelayed(this::sendNextNumber, delaySeconds * 1000L);

        } catch (Exception e) {
            Toast.makeText(this, "Error sending to +" + phone + ": " + e.getMessage(), Toast.LENGTH_SHORT).show();
            currentIndex++;
            handler.postDelayed(this::sendNextNumber, 2000);
        }
    }
}
