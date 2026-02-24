package com.banknotifier

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

object NotificationHistory {
    private const val PREFS_NAME = "BankNotifierHistory"
    private const val KEY_HISTORY = "history"
    private const val MAX_ITEMS = 100
    
    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }
    
    fun add(context: Context, item: NotificationItem) {
        val prefs = getPrefs(context)
        val historyJson = prefs.getString(KEY_HISTORY, "[]") ?: "[]"
        val history = JSONArray(historyJson)
        
        // Add new item
        val itemJson = JSONObject().apply {
            put("id", item.id)
            put("content", item.content)
            put("package", item.packageName)
            put("timestamp", item.timestamp)
            put("success", item.success)
            put("error", item.errorMessage ?: "")
        }
        
        history.put(0, itemJson)
        
        // Keep only last MAX_ITEMS
        val trimmed = JSONArray()
        for (i in 0 until minOf(history.length(), MAX_ITEMS)) {
            trimmed.put(history.get(i))
        }
        
        prefs.edit().putString(KEY_HISTORY, trimmed.toString()).apply()
    }
    
    fun getAll(context: Context): List<NotificationItem> {
        val prefs = getPrefs(context)
        val historyJson = prefs.getString(KEY_HISTORY, "[]") ?: "[]"
        val history = JSONArray(historyJson)
        
        val items = mutableListOf<NotificationItem>()
        for (i in 0 until history.length()) {
            val obj = history.getJSONObject(i)
            items.add(NotificationItem(
                id = obj.getLong("id"),
                content = obj.getString("content"),
                packageName = obj.getString("package"),
                timestamp = obj.getLong("timestamp"),
                success = obj.getBoolean("success"),
                errorMessage = obj.optString("error").takeIf { it.isNotEmpty() }
            ))
        }
        
        return items
    }
    
    fun clear(context: Context) {
        getPrefs(context).edit().putString(KEY_HISTORY, "[]").apply()
    }
}
