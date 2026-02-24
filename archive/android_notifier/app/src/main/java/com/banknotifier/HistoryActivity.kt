package com.banknotifier

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import java.text.SimpleDateFormat
import java.util.*

class HistoryActivity : AppCompatActivity() {
    
    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyState: View
    private lateinit var adapter: HistoryAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_history)
        
        recyclerView = findViewById(R.id.historyRecyclerView)
        emptyState = findViewById(R.id.emptyState)
        val clearButton = findViewById<Button>(R.id.clearButton)
        
        recyclerView.layoutManager = LinearLayoutManager(this)
        
        loadHistory()
        
        clearButton.setOnClickListener {
            NotificationHistory.clear(this)
            loadHistory()
            Toast.makeText(this, "History cleared", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun loadHistory() {
        val items = NotificationHistory.getAll(this)
        
        if (items.isEmpty()) {
            recyclerView.visibility = View.GONE
            emptyState.visibility = View.VISIBLE
        } else {
            recyclerView.visibility = View.VISIBLE
            emptyState.visibility = View.GONE
            adapter = HistoryAdapter(items) { item ->
                resendNotification(item)
            }
            recyclerView.adapter = adapter
        }
    }
    
    private fun resendNotification(item: NotificationItem) {
        val prefs = getSharedPreferences("BankNotifier", MODE_PRIVATE)
        val serverUrl = prefs.getString("server_url", "") ?: ""
        
        if (serverUrl.isEmpty()) {
            Toast.makeText(this, "No server configured", Toast.LENGTH_SHORT).show()
            return
        }
        
        AppExecutors.networkIO.execute {
            try {
                val payload = org.json.JSONObject()
                payload.put("content", item.content)
                payload.put("package", item.packageName)
                
                val success = HttpSender.sendNotification(serverUrl, payload.toString())
                runOnUiThread {
                    if (success) {
                        Toast.makeText(this, "✅ Resent successfully", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(this, "❌ Failed to resend", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    Toast.makeText(this, "❌ Error: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}

class HistoryAdapter(
    private val items: List<NotificationItem>,
    private val onResend: (NotificationItem) -> Unit
) : RecyclerView.Adapter<HistoryAdapter.ViewHolder>() {
    
    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val statusIcon: TextView = view.findViewById(R.id.statusIcon)
        val contentText: TextView = view.findViewById(R.id.contentText)
        val timeText: TextView = view.findViewById(R.id.timeText)
        val resendButton: Button = view.findViewById(R.id.resendButton)
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_notification, parent, false)
        return ViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]
        
        holder.statusIcon.text = if (item.success) "✅" else "❌"
        holder.contentText.text = item.content
        holder.timeText.text = formatTime(item.timestamp)
        
        if (!item.success) {
            holder.resendButton.visibility = View.VISIBLE
            holder.resendButton.setOnClickListener {
                onResend(item)
            }
        } else {
            holder.resendButton.visibility = View.GONE
        }
    }
    
    override fun getItemCount() = items.size
    
    private fun formatTime(timestamp: Long): String {
        val diff = System.currentTimeMillis() - timestamp
        val minutes = diff / 60000
        
        return when {
            minutes < 1 -> "Just now"
            minutes < 60 -> "$minutes min ago"
            minutes < 1440 -> "${minutes / 60}h ago"
            else -> SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault()).format(Date(timestamp))
        }
    }
}
