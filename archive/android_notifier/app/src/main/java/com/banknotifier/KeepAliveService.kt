package com.banknotifier

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat

/**
 * Foreground Service to keep the app alive when screen is locked.
 * Uses START_STICKY to automatically restart if killed by system.
 */
class KeepAliveService : Service() {
    
    companion object {
        private const val TAG = "KeepAliveService"
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "keep_alive_channel"
        
        // Actions
        const val ACTION_START = "com.banknotifier.action.START"
        const val ACTION_STOP = "com.banknotifier.action.STOP"
        
        fun start(context: Context) {
            val intent = Intent(context, KeepAliveService::class.java).apply {
                action = ACTION_START
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stop(context: Context) {
            val intent = Intent(context, KeepAliveService::class.java).apply {
                action = ACTION_STOP
            }
            context.stopService(intent)
        }
    }
    
    private var wakeLock: PowerManager.WakeLock? = null
    private var isServiceRunning = false
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service created")
        createNotificationChannel()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "onStartCommand: action=${intent?.action}")
        
        when (intent?.action) {
            ACTION_STOP -> {
                stopSelf()
                return START_NOT_STICKY
            }
        }
        
        if (!isServiceRunning) {
            isServiceRunning = true
            startForeground(NOTIFICATION_ID, buildNotification())
            acquireWakeLock()
            Log.i(TAG, "Service started in foreground")
        }
        
        // START_STICKY: System will restart service if killed
        return START_STICKY
    }
    
    override fun onDestroy() {
        super.onDestroy()
        isServiceRunning = false
        releaseWakeLock()
        Log.d(TAG, "Service destroyed")
        
        // Attempt to restart if we're supposed to be running
        val prefs = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
        if (prefs.getBoolean("enabled", true)) {
            Log.d(TAG, "Scheduling restart...")
            scheduleRestart()
        }
    }
    
    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        // Only restart if user hasn't explicitly disabled the service
        val prefs = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
        if (prefs.getBoolean("enabled", true)) {
            Log.d(TAG, "Task removed, scheduling restart")
            scheduleRestart()
        } else {
            Log.d(TAG, "Task removed, service disabled - NOT restarting")
        }
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Keep Alive Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Giữ app hoạt động để nhận thông báo ngân hàng"
                setShowBadge(false)
                setSound(null, null)
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    private fun buildNotification(): Notification {
        // Intent để mở app khi tap notification
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        
        // Intent để tắt service
        val stopIntent = Intent(this, KeepAliveService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🏦 Bank Notifier")
            .setContentText("Đang hoạt động - Nhấn để mở")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .setAutoCancel(false)
            .setContentIntent(pendingIntent)
            .addAction(
                android.R.drawable.ic_delete,
                "Tắt",
                stopPendingIntent
            )
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }
    
    private fun acquireWakeLock() {
        try {
            if (wakeLock == null) {
                val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
                wakeLock = powerManager.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK,
                    "BankNotifier::KeepAlive"
                )
            }
            
            if (wakeLock?.isHeld == false) {
                // Acquire with 10-min timeout (watchdog will renew)
                wakeLock?.acquire(10 * 60 * 1000L)
                Log.d(TAG, "WakeLock acquired (10min timeout)")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to acquire WakeLock", e)
        }
    }
    
    private fun releaseWakeLock() {
        try {
            wakeLock?.let {
                if (it.isHeld) {
                    it.release()
                    Log.d(TAG, "WakeLock released")
                }
            }
            wakeLock = null
        } catch (e: Exception) {
            Log.e(TAG, "Failed to release WakeLock", e)
        }
    }
    
    private fun scheduleRestart() {
        try {
            // Use ServiceWatchdog to restart
            ServiceWatchdog.scheduleNextCheck(this)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to schedule restart", e)
        }
    }
}
