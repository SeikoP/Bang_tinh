package com.banknotifier

import android.content.Context
import android.content.SharedPreferences
import java.text.SimpleDateFormat
import java.util.*

object Statistics {
    private const val PREFS_NAME = "BankNotifierStats"
    private const val KEY_SENT_TODAY = "sent_today"
    private const val KEY_SUCCESS_TODAY = "success_today"
    private const val KEY_FAILED_TODAY = "failed_today"
    private const val KEY_LAST_DATE = "last_date"
    private const val KEY_LAST_NOTIFICATION = "last_notification"
    private const val KEY_LAST_CHECK = "last_check"
    
    @Volatile
    private var cachedPrefs: SharedPreferences? = null
    
    private fun getPrefs(context: Context): SharedPreferences {
        return cachedPrefs ?: context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).also {
            cachedPrefs = it
        }
    }
    
    private fun getTodayDate(): String {
        return SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
    }
    
    private fun resetIfNewDay(prefs: SharedPreferences) {
        val lastDate = prefs.getString(KEY_LAST_DATE, "")
        val today = getTodayDate()
        
        if (lastDate != today) {
            prefs.edit()
                .putString(KEY_LAST_DATE, today)
                .putInt(KEY_SENT_TODAY, 0)
                .putInt(KEY_SUCCESS_TODAY, 0)
                .putInt(KEY_FAILED_TODAY, 0)
                .apply()
        }
    }
    
    fun incrementSent(context: Context) {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        val current = prefs.getInt(KEY_SENT_TODAY, 0)
        prefs.edit().putInt(KEY_SENT_TODAY, current + 1).apply()
    }
    
    fun incrementSuccess(context: Context) {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        val current = prefs.getInt(KEY_SUCCESS_TODAY, 0)
        prefs.edit()
            .putInt(KEY_SUCCESS_TODAY, current + 1)
            .putLong(KEY_LAST_NOTIFICATION, System.currentTimeMillis())
            .apply()
    }
    
    fun incrementFailed(context: Context) {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        val current = prefs.getInt(KEY_FAILED_TODAY, 0)
        prefs.edit().putInt(KEY_FAILED_TODAY, current + 1).apply()
    }
    
    fun getSentToday(context: Context): Int {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        return prefs.getInt(KEY_SENT_TODAY, 0)
    }
    
    fun getSuccessToday(context: Context): Int {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        return prefs.getInt(KEY_SUCCESS_TODAY, 0)
    }
    
    fun getFailedToday(context: Context): Int {
        val prefs = getPrefs(context)
        resetIfNewDay(prefs)
        return prefs.getInt(KEY_FAILED_TODAY, 0)
    }
    
    fun getLastNotificationTime(context: Context): Long {
        return getPrefs(context).getLong(KEY_LAST_NOTIFICATION, 0)
    }
    
    fun updateLastCheck(context: Context) {
        getPrefs(context).edit()
            .putLong(KEY_LAST_CHECK, System.currentTimeMillis())
            .apply()
    }
    
    fun getLastCheck(context: Context): Long {
        return getPrefs(context).getLong(KEY_LAST_CHECK, 0)
    }
}
