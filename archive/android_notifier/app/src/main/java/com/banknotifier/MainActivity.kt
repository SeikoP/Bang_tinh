package com.banknotifier

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.LinearLayout
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.provider.Settings
import android.text.TextUtils
import android.widget.Button
import android.widget.EditText
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {
    
    private lateinit var prefs: SharedPreferences
    private lateinit var serverUrlInput: EditText
    private lateinit var enabledSwitch: Switch
    private lateinit var debugSwitch: Switch
    private lateinit var statusText: TextView
    private lateinit var connectionStatus: TextView
    private lateinit var lastSyncText: TextView
    private lateinit var statSent: TextView
    private lateinit var statSuccess: TextView
    private lateinit var statFailed: TextView
    private lateinit var watchdogStatus: TextView
    private lateinit var testButton: Button
    private lateinit var statusCard: LinearLayout
    
    // Connection health tracking
    private var consecutiveFailures = 0
    
    // QR Scanner launcher
    private val qrScannerLauncher = registerForActivityResult(ScanContract()) { result ->
        if (result.contents != null) {
            val scannedContent = result.contents
            try {
                // Try parsing JSON format: {"h": "ip", "p": port, "k": "key"}
                val json = org.json.JSONObject(scannedContent)
                val host = json.optString("h")
                val port = json.optInt("p", 5005)
                val key = json.optString("k", "")
                
                if (host.isNotEmpty()) {
                    val url = "http://$host:$port"
                    serverUrlInput.setText(url)
                    
                    // Save settings
                    prefs.edit()
                        .putString("server_url", url)
                        .putString("auth_token", key)
                        .apply()
                        
                    Toast.makeText(this, "✅ Cấu hình thành công!\nURL: $url\nKey: ${key.take(4)}...", Toast.LENGTH_LONG).show()
                } else {
                    Toast.makeText(this, "❌ Lỗi: QR thiếu thông tin Host (h)", Toast.LENGTH_LONG).show()
                }
            } catch (e: Exception) {
                // Fallback to plain URL format
                if (scannedContent.startsWith("http://") || scannedContent.startsWith("https://")) {
                    serverUrlInput.setText(scannedContent)
                    prefs.edit().putString("server_url", scannedContent).apply()
                    Toast.makeText(this, "⚠️ Định dạng cũ (URL only). Vui lòng dùng bản mới nhất trên PC.", Toast.LENGTH_LONG).show()
                } else {
                    Toast.makeText(this, "❌ Mã QR không hợp lệ.", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
    
    private val handler = Handler(Looper.getMainLooper())
    private val checkConnectionRunnable = object : Runnable {
        override fun run() {
            checkConnection()
            handler.postDelayed(this, 30000) // Check every 30 seconds
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        prefs = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
        
        // Initialize views
        serverUrlInput = findViewById(R.id.serverUrl)
        enabledSwitch = findViewById(R.id.enabledSwitch)
        debugSwitch = findViewById(R.id.debugSwitch)
        statusText = findViewById(R.id.statusText)
        connectionStatus = findViewById(R.id.connectionStatus)
        lastSyncText = findViewById(R.id.lastSyncText)
        statusCard = findViewById(R.id.statusCard)
        statSent = findViewById(R.id.statSent)
        statSuccess = findViewById(R.id.statSuccess)
        statFailed = findViewById(R.id.statFailed)
        watchdogStatus = findViewById(R.id.watchdogStatus)
        testButton = findViewById(R.id.testButton)
        
        val saveButton = findViewById<Button>(R.id.saveButton)
        val scanQrButton = findViewById<Button>(R.id.scanQrButton)
        val permissionButton = findViewById<Button>(R.id.permissionButton)
        val batteryButton = findViewById<Button>(R.id.batteryButton)
        val historyButton = findViewById<Button>(R.id.historyButton)
        
        // Load saved settings
        serverUrlInput.setText(prefs.getString("server_url", "http://192.168.2.17:5005"))
        enabledSwitch.isChecked = prefs.getBoolean("enabled", true)
        debugSwitch.isChecked = prefs.getBoolean("debug_mode", false)
        
        updateStatus()
        updateStatistics()
        
        // Start KeepAlive service if enabled
        if (prefs.getBoolean("enabled", true)) {
            KeepAliveService.start(this)
            ServiceWatchdog.startWatching(this)
        }
        
        saveButton.setOnClickListener {
            val url = serverUrlInput.text.toString()
            if (url.isNotEmpty()) {
                prefs.edit()
                    .putString("server_url", url)
                    .putBoolean("enabled", enabledSwitch.isChecked)
                    .putBoolean("debug_mode", debugSwitch.isChecked)
                    .apply()
                
                val debugMsg = if (debugSwitch.isChecked) " (Debug ON)" else ""
                Toast.makeText(this, "✅ Đã lưu cấu hình$debugMsg", Toast.LENGTH_SHORT).show()
                updateStatus()
                
                // Start or stop KeepAlive service based on enabled state
                if (enabledSwitch.isChecked) {
                    KeepAliveService.start(this)
                    ServiceWatchdog.startWatching(this)
                } else {
                    KeepAliveService.stop(this)
                    ServiceWatchdog.cancelAll(this)
                }
            }
        }
        
        scanQrButton.setOnClickListener {
            val options = ScanOptions()
            options.setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            options.setPrompt("Scan QR code from PC app")
            options.setCameraId(0)
            options.setBeepEnabled(true)
            options.setBarcodeImageEnabled(false)
            options.setOrientationLocked(false)
            qrScannerLauncher.launch(options)
        }
        
        permissionButton.setOnClickListener {
            openNotificationSettings()
        }
        
        testButton.setOnClickListener {
            testConnection()
        }
        
        batteryButton.setOnClickListener {
            openBatteryOptimizationSettings()
        }
        
        val autoStartButton = findViewById<Button>(R.id.autoStartButton)
        autoStartButton?.setOnClickListener {
            openAutoStartSettings()
        }
        
        historyButton.setOnClickListener {
            startActivity(Intent(this, HistoryActivity::class.java))
        }
        
        // Remote Input button - opens session editor
        val remoteInputButton = findViewById<Button>(R.id.remoteInputButton)
        remoteInputButton.setOnClickListener {
            startActivity(Intent(this, RemoteInputActivity::class.java))
        }

        val appGuardianButton = findViewById<Button>(R.id.appGuardianButton)
        appGuardianButton.setOnClickListener {
            startActivity(Intent(this, AppSelectorActivity::class.java))
        }
        
        // Test Sample Notification button
        val testSampleButton = findViewById<Button>(R.id.testSampleButton)
        testSampleButton?.setOnClickListener {
            sendSampleNotification()
        }
        
        // Exit App button - complete shutdown
        val exitAppButton = findViewById<Button>(R.id.exitAppButton)
        exitAppButton.setOnClickListener {
            exitApp()
        }

        // Start periodic connection check
        handler.post(checkConnectionRunnable)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacks(checkConnectionRunnable)
    }
    
    override fun onResume() {
        super.onResume()
        updateStatus()
        updateStatistics()
        updateLastSync()
    }
    
    private fun updateStatistics() {
        statSent.text = Statistics.getSentToday(this).toString()
        statSuccess.text = Statistics.getSuccessToday(this).toString()
        statFailed.text = Statistics.getFailedToday(this).toString()
    }
    
    private fun updateLastSync() {
        val lastCheck = Statistics.getLastCheck(this)
        if (lastCheck > 0) {
            val diff = System.currentTimeMillis() - lastCheck
            val minutes = diff / 60000
            lastSyncText.text = when {
                minutes < 1 -> "Kiểm tra cuối: Vừa xong"
                minutes < 60 -> "Kiểm tra cuối: $minutes phút trước"
                else -> "Kiểm tra cuối: ${minutes / 60} giờ trước"
            }
        } else {
            lastSyncText.text = "Kiểm tra cuối: Chưa bao giờ"
        }
    }
    
    private fun checkConnection() {
        val url = serverUrlInput.text.toString()
        if (url.isEmpty()) {
            connectionStatus.text = "🔴 No server configured"
            return
        }
        
        AppExecutors.networkIO.execute {
            try {
                val testJson = org.json.JSONObject()
                testJson.put("content", "Ping")
                testJson.put("package", "com.banknotifier")
                
                val token = prefs.getString("auth_token", "")
                val success = HttpSender.sendNotification(url, testJson.toString(), token)
                Statistics.updateLastCheck(this)
                
                runOnUiThread {
                    if (success) {
                        consecutiveFailures = 0
                        connectionStatus.text = "🟢 Đã kết nối"
                        statusCard.setBackgroundResource(R.drawable.bg_input_rounded)
                    } else {
                        consecutiveFailures++
                        connectionStatus.text = if (consecutiveFailures >= 3)
                            "🔴 Mất kết nối ($consecutiveFailures lần thất bại)"
                        else
                            "🟡 Không thể kết nối server"
                        if (consecutiveFailures >= 3) {
                            statusCard.setBackgroundColor(0xFFFEF2F2.toInt()) // Light red tint
                        }
                    }
                    updateLastSync()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    consecutiveFailures++
                    connectionStatus.text = if (consecutiveFailures >= 3)
                        "🔴 Mất kết nối ($consecutiveFailures lần thất bại)"
                    else
                        "🔴 Lỗi kết nối"
                    if (consecutiveFailures >= 3) {
                        statusCard.setBackgroundColor(0xFFFEF2F2.toInt())
                    }
                    updateLastSync()
                }
            }
        }
    }
    
    private fun updateStatus() {
        val hasPermission = isNotificationServiceEnabled()
        val enabled = prefs.getBoolean("enabled", true)
        val isBatteryOptimized = isBatteryOptimized()
        
        statusText.text = when {
            !hasPermission -> "❌ Chưa cấp quyền thông báo"
            !enabled -> "⏸️ Đang tạm dừng"
            isBatteryOptimized -> "⚠️ Bị tối ưu pin (Dễ bị kill)"
            else -> "✅ Đang hoạt động"
        }
        
        // Cập nhật trạng thái Watchdog hiển thị trên UI
        if (enabled) {
            watchdogStatus.visibility = android.view.View.VISIBLE
            watchdogStatus.text = "🛡️ Watchdog: Đang bảo vệ (2p/lần)"
        } else {
            watchdogStatus.visibility = android.view.View.GONE
        }
    }
    
    private fun isBatteryOptimized(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            return !pm.isIgnoringBatteryOptimizations(packageName)
        }
        return false
    }
    
    private fun openBatteryOptimizationSettings() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            try {
                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                intent.data = Uri.parse("package:$packageName")
                startActivity(intent)
                Toast.makeText(this, "⚠️ QUAN TRỌNG: Nếu không thấy app trong danh sách, hãy đổi bộ lọc thành 'TẤT CẢ ỨNG DỤNG'. Sau đó tìm app này và chọn 'KHÔNG HẠN CHẾ' (Unrestricted).", Toast.LENGTH_LONG).show()
            } catch (e: Exception) {
                // Fallback to general battery settings
                val fallbackIntent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                startActivity(fallbackIntent)
                Toast.makeText(this, "💡 Chọn 'Tất cả ứng dụng' -> Tìm app này -> Chọn 'Không hạn chế'", Toast.LENGTH_LONG).show()
            }
        } else {
            Toast.makeText(this, "Không cần thiết trên phiên bản Android này", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun openAutoStartSettings() {
        val intent = Intent()
        val manufacturer = Build.MANUFACTURER.lowercase()
        try {
            when {
                manufacturer.contains("xiaomi") -> intent.component = ComponentName("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity")
                manufacturer.contains("oppo") -> intent.component = ComponentName("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity")
                manufacturer.contains("vivo") -> intent.component = ComponentName("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity")
                manufacturer.contains("letv") -> intent.component = ComponentName("com.letv.android.letvsafe", "com.letv.android.letvsafe.AutobootManageActivity")
                manufacturer.contains("honor") -> intent.component = ComponentName("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity")
                else -> {
                    intent.action = Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                    intent.data = Uri.parse("package:$packageName")
                }
            }
            startActivity(intent)
            Toast.makeText(this, "💡 Hãy bật 'Tự khởi chạy' (Auto-start) cho app", Toast.LENGTH_LONG).show()
        } catch (e: Exception) {
            val detailIntent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            detailIntent.data = Uri.parse("package:$packageName")
            startActivity(detailIntent)
        }
    }
    
    private fun isNotificationServiceEnabled(): Boolean {
        val pkgName = packageName
        val flat = Settings.Secure.getString(
            contentResolver,
            "enabled_notification_listeners"
        )
        if (!TextUtils.isEmpty(flat)) {
            val names = flat.split(":")
            for (name in names) {
                val cn = ComponentName.unflattenFromString(name)
                if (cn != null && TextUtils.equals(pkgName, cn.packageName)) {
                    return true
                }
            }
        }
        return false
    }
    
    private fun openNotificationSettings() {
        val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        startActivity(intent)
    }
    
    private fun testConnection() {
        val url = serverUrlInput.text.toString()
        if (url.isEmpty()) {
            Toast.makeText(this, "Please enter server URL", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            Toast.makeText(this, "URL must start with http:// or https://", Toast.LENGTH_LONG).show()
            return
        }
        
        if (url.startsWith("https://") && (url.contains("192.168.") || url.contains("10.") || url.contains("172."))) {
            Toast.makeText(this, "⚠️ HTTPS with local IP may not work. Use HTTP", Toast.LENGTH_LONG).show()
        }
        
        testButton.isEnabled = false
        testButton.text = "Testing..."
        
        AppExecutors.networkIO.execute {
            try {
                val testJson = org.json.JSONObject()
                testJson.put("content", "Ping")
                testJson.put("package", "com.banknotifier")
                testJson.put("title", "Test")
                testJson.put("text", "Connection test")
                
                val token = prefs.getString("auth_token", "")
                val result = HttpSender.sendNotification(url, testJson.toString(), token)
                runOnUiThread {
                    testButton.isEnabled = true
                    testButton.text = "🧪 Thử kết nối"
                    if (result) {
                        consecutiveFailures = 0
                        Toast.makeText(this, "✅ Đã gửi! Hãy nhìn vào GÓC TRÊN CÙNG máy tính để thấy thông báo màu xanh.", Toast.LENGTH_LONG).show()
                        connectionStatus.text = "🟢 Đã kết nối"
                        statusCard.setBackgroundResource(R.drawable.bg_input_rounded)
                        Statistics.updateLastCheck(this)
                        updateLastSync()
                    } else {
                        Toast.makeText(this, "❌ Không thấy máy tính phản hồi. Hãy kiểm tra:\n- Cùng mạng WiFi\n- Đúng địa chỉ URL\n- App trên máy tính đang mở", Toast.LENGTH_LONG).show()
                        connectionStatus.text = "🔴 Thất bại"
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    testButton.isEnabled = true
                    testButton.text = "🧪 Thử kết nối"
                    Toast.makeText(this, "❌ Lỗi: ${e.message}", Toast.LENGTH_LONG).show()
                    connectionStatus.text = "🔴 Lỗi"
                }
            }
        }
    }
    
    private fun sendSampleNotification() {
        val url = serverUrlInput.text.toString()
        if (url.isEmpty()) {
            Toast.makeText(this, "Vui lòng nhập Server URL trước", Toast.LENGTH_SHORT).show()
            return
        }
        
        AppExecutors.networkIO.execute {
            try {
                // Sample bank notification with realistic data
                val sampleJson = org.json.JSONObject()
                sampleJson.put("content", "VietinBank: +5,000,000 VND tu NGUYEN VAN A. SD: 12,345,678 VND. Tai 192.168.1.100 luc 13:14 08/02")
                sampleJson.put("package", "com.vietinbank.ipay")
                sampleJson.put("title", "VietinBank")
                sampleJson.put("text", "+5,000,000 VND tu NGUYEN VAN A")
                
                val token = prefs.getString("auth_token", "")
                val result = HttpSender.sendNotification(url, sampleJson.toString(), token)
                
                runOnUiThread {
                    if (result) {
                        Toast.makeText(this, "✅ Đã gửi thông báo mẫu! Kiểm tra màn hình PC.", Toast.LENGTH_LONG).show()
                    } else {
                        Toast.makeText(this, "❌ Không gửi được. Kiểm tra kết nối.", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    Toast.makeText(this, "❌ Lỗi: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    /**
     * Completely exit the app: stop all services, cancel watchdog, prevent auto-restart.
     * Shows a confirmation dialog first.
     */
    private fun exitApp() {
        AlertDialog.Builder(this)
            .setTitle("⏹️ Tắt hoàn toàn?")
            .setMessage(
                "Tất cả dịch vụ sẽ bị dừng:\n\n" +
                "• Dừng chuyển tiếp thông báo\n" +
                "• Tắt Watchdog bảo vệ\n" +
                "• Tắt KeepAlive service\n\n" +
                "Bạn sẽ KHÔNG nhận được thông báo ngân hàng cho đến khi mở lại app."
            )
            .setPositiveButton("Tắt hoàn toàn") { _, _ ->
                // 1. Disable auto-restart flag
                prefs.edit()
                    .putBoolean("enabled", false)
                    .apply()

                // 2. Cancel watchdog alarms (must be done BEFORE stopping service)
                ServiceWatchdog.cancelAll(this)

                // 3. Stop KeepAlive foreground service
                KeepAliveService.stop(this)

                // 4. Remove periodic connection check
                handler.removeCallbacks(checkConnectionRunnable)

                // 5. Toast confirmation
                Toast.makeText(this, "✅ Đã tắt hoàn toàn. Mở lại app khi cần.", Toast.LENGTH_LONG).show()

                // 6. Close all activities
                finishAffinity()
            }
            .setNegativeButton("Hủy", null)
            .show()
    }
}
