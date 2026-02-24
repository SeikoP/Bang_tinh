package com.banknotifier

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.SystemClock
import android.util.Log

/**
 * Watchdog to ensure KeepAliveService is always running.
 * Uses AlarmManager to periodically check and restart services.
 */
class ServiceWatchdog : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "ServiceWatchdog"
        private const val CHECK_INTERVAL_MS = 2 * 60 * 1000L // 2 minutes
        private const val REQUEST_CODE = 2001
        
        /**
         * Schedule the next watchdog check
         */
        fun scheduleNextCheck(context: Context) {
            try {
                val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
                val intent = Intent(context, ServiceWatchdog::class.java)
                val pendingIntent = PendingIntent.getBroadcast(
                    context,
                    REQUEST_CODE,
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                
                val triggerTime = SystemClock.elapsedRealtime() + CHECK_INTERVAL_MS
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    alarmManager.setExactAndAllowWhileIdle(
                        AlarmManager.ELAPSED_REALTIME_WAKEUP,
                        triggerTime,
                        pendingIntent
                    )
                } else {
                    alarmManager.setExact(
                        AlarmManager.ELAPSED_REALTIME_WAKEUP,
                        triggerTime,
                        pendingIntent
                    )
                }
                
                Log.d(TAG, "Scheduled next check in ${CHECK_INTERVAL_MS / 1000}s")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to schedule next check", e)
            }
        }
        
        /**
         * Cancel all scheduled checks
         */
        fun cancelAll(context: Context) {
            try {
                val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
                val intent = Intent(context, ServiceWatchdog::class.java)
                val pendingIntent = PendingIntent.getBroadcast(
                    context,
                    REQUEST_CODE,
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                alarmManager.cancel(pendingIntent)
                Log.d(TAG, "Cancelled all scheduled checks")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to cancel checks", e)
            }
        }
        
        /**
         * Start watching immediately
         */
        fun startWatching(context: Context) {
            // First, do an immediate check
            checkAndRestartServices(context)
            // Then schedule periodic checks
            scheduleNextCheck(context)
        }
        
        /**
         * Check if services are running and restart if needed
         */
        fun checkAndRestartServices(context: Context) {
            val prefs = context.getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
            
            // Only restart if service should be enabled
            if (!prefs.getBoolean("enabled", true)) {
                Log.d(TAG, "Service disabled, not restarting")
                return
            }
            
            Log.d(TAG, "Checking service status...")
            
            // Start KeepAliveService
            KeepAliveService.start(context)
            
            // WAKE UP GUARDED APPS
            wakeUpGuardedApps(context)
            
            Log.d(TAG, "Restart signal and App WakeUp sent")
        }

        /**
         * Sends a "poke" intent to selected apps to keep them out of hibernation
         */
        private fun wakeUpGuardedApps(context: Context) {
            // Disabled to prevent intrusive behavior during testing
            /*
            try {
                val prefs = context.getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
                val appPackages = prefs.getStringSet("guarded_apps", emptySet()) ?: emptySet()
                
                if (appPackages.isEmpty()) return

                val pm = context.packageManager
                for (pkg in appPackages) {
                    try {
                        val intent = pm.getLaunchIntentForPackage(pkg)
                        if (intent != null) {
                            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            intent.addFlags(Intent.FLAG_ACTIVITY_NO_USER_ACTION)
                            intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION)
                            context.startActivity(intent)
                            Log.d(TAG, "Poked app: $pkg")
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to poke app $pkg: ${e.message}")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in wakeUpGuardedApps: ${e.message}")
            }
            */
        }
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        Log.d(TAG, "Watchdog triggered")
        
        // Check and restart services
        checkAndRestartServices(context)
        
        // Schedule next check
        scheduleNextCheck(context)
    }
}
