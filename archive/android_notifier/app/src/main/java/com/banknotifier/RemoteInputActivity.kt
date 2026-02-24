package com.banknotifier

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import android.os.Build
import org.json.JSONArray
import org.json.JSONObject
import java.text.NumberFormat
import java.util.*

/**
 * Remote Input Activity - Nhập chốt ca từ điện thoại
 * Connects to PC app to get/update session data
 */
class RemoteInputActivity : AppCompatActivity() {
    
    private lateinit var recyclerView: RecyclerView
    private lateinit var statusText: TextView
    private lateinit var totalText: TextView
    private lateinit var refreshButton: Button
    private lateinit var saveButton: Button
    private lateinit var loadingProgress: ProgressBar
    
    private lateinit var adapter: SessionAdapter
    private val sessionItems = mutableListOf<SessionItem>()
    
    // Scratchpad UI
    private lateinit var scratchpadOverlay: View
    private lateinit var scratchpadView: ScratchpadView
    private lateinit var btnScratchpad: Button
    private lateinit var btnClearScratchpad: Button
    private lateinit var btnCloseScratchpad: Button
    
    // Gesture Detection
    private lateinit var gestureDetector: android.view.GestureDetector
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_remote_input)
        
        supportActionBar?.title = "📋 Nhập Chốt Ca"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        
        // Initialize views
        recyclerView = findViewById(R.id.sessionRecyclerView)
        statusText = findViewById(R.id.statusText)
        totalText = findViewById(R.id.totalText)
        refreshButton = findViewById(R.id.refreshButton)
        saveButton = findViewById(R.id.saveButton)
        loadingProgress = findViewById(R.id.loadingProgress)
        
        // Scratchpad initialization
        scratchpadOverlay = findViewById(R.id.scratchpadOverlay)
        scratchpadView = findViewById(R.id.scratchpadView)
        btnScratchpad = findViewById(R.id.btnScratchpad)
        btnClearScratchpad = findViewById(R.id.btnClearScratchpad)
        btnCloseScratchpad = findViewById(R.id.btnCloseScratchpad)
        
        // Setup Swipe Gesture Detector
        setupGestureDetector()
        
        // Setup RecyclerView
        adapter = SessionAdapter(sessionItems) { position, newClosingQty ->
            sessionItems[position].closingQty = newClosingQty
            updateTotal()
        }
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter
        
        // Button listeners
        refreshButton.setOnClickListener { loadSessionData() }
        saveButton.setOnClickListener { saveSessionData() }
        
        // Scratchpad listeners
        btnScratchpad.setOnClickListener {
            showScratchpad(true)
        }
        btnClearScratchpad.setOnClickListener {
            scratchpadView.clear()
        }
        btnCloseScratchpad.setOnClickListener {
            showScratchpad(false)
        }
        
        // Load data on start
        loadSessionData()
    }

    private fun setupGestureDetector() {
        val listener = object : android.view.GestureDetector.SimpleOnGestureListener() {
            override fun onFling(
                e1: android.view.MotionEvent?,
                e2: android.view.MotionEvent,
                velocityX: Float,
                velocityY: Float
            ): Boolean {
                if (e1 == null) return false
                val deltaX = e2.x - e1.x
                val deltaY = e2.y - e1.y
                
                // Detect horizontal swipe (horizontal distance > vertical distance)
                if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 300 && Math.abs(velocityX) > 1000) {
                    showScratchpad(true)
                    return true
                }
                return false
            }
        }
        gestureDetector = android.view.GestureDetector(this, listener)
    }

    override fun dispatchTouchEvent(ev: android.view.MotionEvent?): Boolean {
        // If scratchpad is visible, let it handle touches (drawing)
        if (scratchpadOverlay.visibility == View.VISIBLE) {
            return super.dispatchTouchEvent(ev)
        }
        // Otherwise, prioritize gesture detector for swipe opening
        gestureDetector.onTouchEvent(ev!!)
        return super.dispatchTouchEvent(ev)
    }

    private fun showScratchpad(show: Boolean) {
        scratchpadOverlay.visibility = if (show) View.VISIBLE else View.GONE
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
    
    private fun getServerUrl(): String {
        val prefs = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
        var url = prefs.getString("server_url", "") ?: ""
        
        // Auto-fix URL format if user entered raw IP or partially correct URL
        if (url.isNotEmpty()) {
            if (!url.startsWith("http")) {
                url = "http://$url"
            }
            // Auto-append port if missing
            if (!url.contains(":5005") && url.count { it == ':' } < 2) {
                url = "$url:5005"
            }
        }
        return url
    }
    
    private fun showLoading(show: Boolean) {
        runOnUiThread {
            loadingProgress.visibility = if (show) View.VISIBLE else View.GONE
            recyclerView.visibility = if (show) View.GONE else View.VISIBLE
            refreshButton.isEnabled = !show
            saveButton.isEnabled = !show
        }
    }
    
    private fun showStatus(message: String, isError: Boolean = false) {
        runOnUiThread {
            statusText.text = message
            val colorRes = if (isError) android.R.color.holo_red_dark else android.R.color.holo_green_dark
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                statusText.setTextColor(resources.getColor(colorRes, null))
            } else {
                @Suppress("DEPRECATION")
                statusText.setTextColor(resources.getColor(colorRes))
            }
        }
    }
    
    private fun loadSessionData() {
        val serverUrl = getServerUrl()
        if (serverUrl.isEmpty()) {
            showStatus("❌ Chưa cấu hình server URL. Vui lòng quét mã QR ở màn hình chính.", true)
            return
        }
        
        showLoading(true)
        showStatus("Đang tải dữ liệu...")
        
        val token = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE).getString("auth_token", "")
        
        AppExecutors.networkIO.execute {
            try {
                val apiUrl = serverUrl.trimEnd('/') + "/api/session"
                val response = HttpSender.get(apiUrl, token)
                
                if (response != null && response.isNotEmpty()) {
                    // Validate response is JSON before parsing
                    if (!response.trim().startsWith("{") && !response.trim().startsWith("[")) {
                        runOnUiThread {
                            showLoading(false)
                            showStatus("❌ Lỗi: Server trả về dữ liệu không hợp lệ")
                            Toast.makeText(this, "Server response không phải JSON: ${response.take(50)}", Toast.LENGTH_LONG).show()
                        }
                        return@execute
                    }
                    
                    val json = org.json.JSONObject(response)
                    
                    if (json.getBoolean("success")) {
                        val sessionArray = json.getJSONArray("session")
                        val newList = mutableListOf<SessionItem>()
                        
                        for (i in 0 until sessionArray.length()) {
                            val item = sessionArray.getJSONObject(i)
                            newList.add(SessionItem(
                                productId = item.getInt("product_id"),
                                productName = item.getString("product_name"),
                                largeUnit = item.getString("large_unit"),
                                conversion = item.getInt("conversion"),
                                unitPrice = item.getDouble("unit_price"),
                                unitChar = item.getString("unit_char"),
                                handoverQty = item.getInt("handover_qty"),
                                closingQty = item.getInt("closing_qty"),
                                usedQty = item.getInt("used_qty"),
                                amount = item.getDouble("amount")
                            ))
                        }
                        
                        runOnUiThread {
                            sessionItems.clear()
                            sessionItems.addAll(newList)
                            adapter.notifyDataSetChanged()
                            showLoading(false)
                            showStatus("✅ Đã tải ${sessionItems.size} sản phẩm")
                            updateTotal()
                        }
                    } else {
                        val error = json.optString("error", "Unknown")
                        runOnUiThread {
                            showLoading(false)
                            showStatus("❌ Lỗi: $error", true)
                            if (error.contains("Auth")) {
                                Toast.makeText(this@RemoteInputActivity, "⚠️ Lỗi xác thực! Vui lòng quét lại mã QR mới nhất.", Toast.LENGTH_LONG).show()
                            }
                        }
                    }
                } else {
                    runOnUiThread {
                        showLoading(false)
                        showStatus("❌ Không thể kết nối đến PC", true)
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    showLoading(false)
                    showStatus("❌ Lỗi: ${e.message}", true)
                }
            }
        }
    }
    
    private fun saveSessionData() {
        val serverUrl = getServerUrl()
        if (serverUrl.isEmpty()) {
            showStatus("❌ Chưa cấu hình server URL. Vui lòng quét mã QR ở màn hình chính.", true)
            return
        }
        
        showLoading(true)
        showStatus("Đang lưu...")
        
        val token = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE).getString("auth_token", "")
        
        // Take a snapshot of updates to send to avoid concurrent modification
        val itemsSnapshot = sessionItems.map { it.copy() }
        
        AppExecutors.networkIO.execute {
            try {
                val apiUrl = serverUrl.trimEnd('/') + "/api/session"
                
                // Build JSON payload
                val updates = JSONArray()
                for (item in itemsSnapshot) {
                    val update = JSONObject()
                    update.put("product_id", item.productId)
                    update.put("closing_qty", item.closingQty)
                    updates.put(update)
                }
                
                val payload = org.json.JSONObject()
                payload.put("updates", updates)
                
                val success = HttpSender.postJson(apiUrl, payload.toString(), token)
                
                runOnUiThread {
                    showLoading(false)
                    if (success) {
                        showStatus("✅ Đã lưu thành công!")
                        Toast.makeText(this@RemoteInputActivity, "✅ Đã cập nhật chốt ca!", Toast.LENGTH_SHORT).show()
                        // Reload to get updated calculations
                        loadSessionData()
                    } else {
                        showStatus("❌ Không thể lưu dữ liệu (Lỗi Auth hoặc Mạng)", true)
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    showLoading(false)
                    showStatus("❌ Lỗi: ${e.message}", true)
                }
            }
        }
    }
    
    private fun updateTotal() {
        var total = 0.0
        for (item in sessionItems) {
            val used = maxOf(0, item.handoverQty - item.closingQty)
            total += used * item.unitPrice
        }
        
        val formatter = NumberFormat.getCurrencyInstance(Locale("vi", "VN"))
        totalText.text = "Tổng: ${formatter.format(total)}"
    }
}

/**
 * Data class for session item
 */
data class SessionItem(
    val productId: Int,
    val productName: String,
    val largeUnit: String,
    val conversion: Int,
    val unitPrice: Double,
    val unitChar: String,
    val handoverQty: Int,
    var closingQty: Int,
    var usedQty: Int,
    var amount: Double
)

/**
 * RecyclerView Adapter for session items
 */
class SessionAdapter(
    private val items: List<SessionItem>,
    private val onClosingChanged: (Int, Int) -> Unit
) : RecyclerView.Adapter<SessionAdapter.ViewHolder>() {
    
    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val productName: TextView = view.findViewById(R.id.productName)
        val handoverText: TextView = view.findViewById(R.id.handoverText)
        val closingInput: EditText = view.findViewById(R.id.closingInput)
        val usedText: TextView = view.findViewById(R.id.usedText)
        val amountText: TextView = view.findViewById(R.id.amountText)
        val minusBtn: Button = view.findViewById(R.id.minusBtn)
        val plusBtn: Button = view.findViewById(R.id.plusBtn)
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_session, parent, false)
        return ViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]
        val formatter = NumberFormat.getCurrencyInstance(Locale("vi", "VN"))
        
        holder.productName.text = item.productName
        // Format: "4t19" instead of "Giao: 4t19" to save space
        holder.handoverText.text = "↓ ${formatQty(item.handoverQty, item.conversion, item.unitChar)}"
        holder.closingInput.setText(formatQty(item.closingQty, item.conversion, item.unitChar))
        
        updateCalculations(holder, item)
        
        // Handle input changes with auto-format
        holder.closingInput.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus) {
                val inputText = holder.closingInput.text.toString()
                val newQty = parseQty(inputText, item.conversion)
                
                // Auto-format to "4t9" style
                val formatted = formatQty(newQty, item.conversion, item.unitChar)
                holder.closingInput.setText(formatted)
                
                if (newQty != item.closingQty) {
                    onClosingChanged(position, newQty)
                    updateCalculations(holder, item.copy(closingQty = newQty))
                }
            }
        }
        
        // Plus/minus buttons
        holder.minusBtn.setOnClickListener {
            val current = item.closingQty
            if (current > 0) {
                val newQty = current - 1
                onClosingChanged(position, newQty)
                holder.closingInput.setText(formatQty(newQty, item.conversion, item.unitChar))
                updateCalculations(holder, item.copy(closingQty = newQty))
            }
        }
        
        holder.plusBtn.setOnClickListener {
            val current = item.closingQty
            if (current < item.handoverQty) {
                val newQty = current + 1
                onClosingChanged(position, newQty)
                holder.closingInput.setText(formatQty(newQty, item.conversion, item.unitChar))
                updateCalculations(holder, item.copy(closingQty = newQty))
            }
        }
    }
    
    override fun getItemCount() = items.size
    
    private fun updateCalculations(holder: ViewHolder, item: SessionItem) {
        val used = maxOf(0, item.handoverQty - item.closingQty)
        val amount = used * item.unitPrice
        
        val formatter = NumberFormat.getCurrencyInstance(Locale("vi", "VN"))
        // Format: "↑ 1" instead of "Đã dùng: 1" to save space
        holder.usedText.text = "↑ ${formatQty(used, item.conversion, item.unitChar)}"
        holder.amountText.text = formatter.format(amount).replace("₫", "đ")
    }
    
    private fun formatQty(qty: Int, conversion: Int, unitChar: String): String {
        if (conversion <= 1) return qty.toString()
        val large = qty / conversion
        val small = qty % conversion
        return if (small == 0) "$large$unitChar" else "$large$unitChar$small"
    }
    
    private fun parseQty(input: String, conversion: Int): Int {
        val cleaned = input.trim().lowercase()
        if (cleaned.isEmpty()) return 0
        
        // Handle different input formats:
        // "4.9" or "4,9" -> 4t9 (4 thùng 9 chai)
        // "4t9" or "4T9" -> 4t9
        // "97" -> 97 chai (if conversion > 1, treat as small units)
        
        // Try format: "4.9" or "4,9" (decimal separator)
        if (cleaned.contains(".") || cleaned.contains(",")) {
            val parts = cleaned.split(Regex("[.,]"))
            if (parts.size == 2) {
                val large = parts[0].toIntOrNull() ?: 0
                val small = parts[1].toIntOrNull() ?: 0
                return (large * conversion) + small
            }
        }
        
        // Try format: "4t9" or "4T9" (with unit char)
        val regex = Regex("(\\d+)[a-z](\\d+)")
        val match = regex.find(cleaned)
        if (match != null) {
            val large = match.groups[1]?.value?.toIntOrNull() ?: 0
            val small = match.groups[2]?.value?.toIntOrNull() ?: 0
            return (large * conversion) + small
        }
        
        // Plain number - treat as small units (chai)
        return cleaned.toIntOrNull() ?: 0
    }
}
