package com.banknotifier

import android.content.Context
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

class NotificationListenerService : NotificationListenerService() {
    
    companion object {
        private const val TAG = "BankNotifier"
    }
    
    private val prefs by lazy { getSharedPreferences("BankNotifier", Context.MODE_PRIVATE) }
    
    override fun onNotificationPosted(sbn: StatusBarNotification) {
        try {
            // Check if service is enabled
            if (!prefs.getBoolean("enabled", true)) {
                return
            }
            
            val debugMode = prefs.getBoolean("debug_mode", false)
            
            // Debug mode: log notification details
            if (debugMode) {
                Log.d(TAG, "=== Notification received ===")
                Log.d(TAG, "Package: ${sbn.packageName}")
                Log.d(TAG, "ID: ${sbn.id}")
            }
            
            val notification = sbn.notification
            val extras = notification.extras
            
            val title = extras.getCharSequence("android.title")?.toString() ?: ""
            val text = extras.getCharSequence("android.text")?.toString() ?: ""
            val bigText = extras.getCharSequence("android.bigText")?.toString() ?: text
            
            // Build structured notification with package info
            val fullContent = if (title.isNotEmpty()) {
                "$title: $bigText"
            } else {
                bigText
            }
            
            if (fullContent.isNotEmpty()) {
                // Send ALL notifications to PC, let PC filter
                // Include package name so PC can decide what to do
                val payload = mapOf(
                    "content" to fullContent,
                    "package" to sbn.packageName,
                    "title" to title,
                    "text" to bigText
                )
                
                if (debugMode) {
                    Log.d(TAG, "Sending notification: $fullContent")
                }
                
                sendToServer(payload)
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error processing notification", e)
        }
    }
    
    private fun sendToServer(payload: Map<String, String>) {
        val serverUrl = prefs.getString("server_url", "") ?: ""
        
        if (serverUrl.isEmpty()) {
            Log.w(TAG, "Server URL not configured")
            return
        }
        
        // Increment sent counter
        Statistics.incrementSent(this)
        
        // Gửi trong background thread pool (tránh tạo Thread mới mỗi notification)
        AppExecutors.networkIO.execute {
            try {
                // Convert to JSON properly
                val jsonPayload = org.json.JSONObject(payload as Map<*, *>).toString()
                
                val token = prefs.getString("auth_token", "")
                val success = HttpSender.sendNotification(serverUrl, jsonPayload, token)
                
                if (success) {
                    Log.d(TAG, "Notification sent successfully")
                    Statistics.incrementSuccess(this)
                    
                    // Save to history
                    NotificationHistory.add(this, NotificationItem(
                        id = System.currentTimeMillis(),
                        content = payload["content"] ?: "",
                        packageName = payload["package"] ?: "",
                        timestamp = System.currentTimeMillis(),
                        success = true
                    ))
                } else {
                    Log.e(TAG, "Failed to send notification")
                    Statistics.incrementFailed(this)
                    
                    // Save failed to history
                    NotificationHistory.add(this, NotificationItem(
                        id = System.currentTimeMillis(),
                        content = payload["content"] ?: "",
                        packageName = payload["package"] ?: "",
                        timestamp = System.currentTimeMillis(),
                        success = false,
                        errorMessage = "Server returned error"
                    ))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error sending notification", e)
                Statistics.incrementFailed(this)
                
                // Save error to history
                NotificationHistory.add(this, NotificationItem(
                    id = System.currentTimeMillis(),
                    content = payload["content"] ?: "",
                    packageName = payload["package"] ?: "",
                    timestamp = System.currentTimeMillis(),
                    success = false,
                    errorMessage = e.message
                ))
            }
        }
    }
    
    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // Không cần xử lý
    }
}
