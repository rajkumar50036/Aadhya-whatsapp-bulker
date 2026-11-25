package com.aadhya.whatsappbulker;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.ViewHolder> {

    private final List<HistoryItem> items;

    public HistoryAdapter(List<HistoryItem> items) {
        this.items = items;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_history, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        HistoryItem item = items.get(position);
        holder.txtPhone.setText("+" + item.getPhone());
        holder.txtMessage.setText(item.getMessage());
        holder.txtTime.setText(item.getTimestamp());
        holder.txtStatus.setText(item.getStatus());

        if (item.getMediaName() != null && !item.getMediaName().isEmpty()) {
            holder.txtMedia.setVisibility(View.VISIBLE);
            holder.txtMedia.setText("📎 " + item.getMediaName());
        } else {
            holder.txtMedia.setVisibility(View.GONE);
        }
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {
        TextView txtPhone, txtMessage, txtTime, txtStatus, txtMedia;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            txtPhone = itemView.findViewById(R.id.txtItemPhone);
            txtMessage = itemView.findViewById(R.id.txtItemMessage);
            txtTime = itemView.findViewById(R.id.txtItemTime);
            txtStatus = itemView.findViewById(R.id.txtItemStatus);
            txtMedia = itemView.findViewById(R.id.txtItemMedia);
        }
    }
}
