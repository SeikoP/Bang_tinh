package com.banknotifier

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.d("BootReceiver", "Device booted, checking if service should start")
            
            val prefs = context.getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
            val enabled = prefs.getBoolean("enabled", true)
            
            if (enabled) {
                Log.d("BootReceiver", "Service enabled, starting KeepAliveService")
                
                // Start KeepAlive service to keep app running
                KeepAliveService.start(context)
                
                // Start watchdog for auto-restart
                ServiceWatchdog.startWatching(context)
                
                Log.d("BootReceiver", "All services started successfully")
            }
        }
    }
}

