package com.banknotifier

import android.util.Log
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.net.URL
import java.util.concurrent.TimeUnit

object HttpSender {
    
    private const val TAG = "HttpSender"
    
    private val client by lazy {
        OkHttpClient.Builder()
            .connectTimeout(3, TimeUnit.SECONDS)
            .writeTimeout(3, TimeUnit.SECONDS)
            .readTimeout(3, TimeUnit.SECONDS)
            .retryOnConnectionFailure(false)
            .build()
    }
    
    fun sendNotification(serverUrl: String, payload: String, authToken: String? = null, maxRetries: Int = 2): Boolean {
        var lastException: Exception? = null
        
        for (attempt in 1..maxRetries) {
            try {
                if (attempt > 1) {
                    Log.d(TAG, "Retry attempt $attempt/$maxRetries")
                    Thread.sleep(1000L * attempt) // Exponential backoff
                }
                
                Log.d(TAG, "Attempting to send to: $serverUrl")
                Log.d(TAG, "Payload: ${payload.take(100)}")
                
                // Validate URL để tránh SSRF attack
                if (!isValidUrl(serverUrl)) {
                    Log.w(TAG, "Invalid URL: $serverUrl")
                    return false
                }
                
                // Payload should already be valid JSON from caller
                val requestBody = payload.toRequestBody("application/json; charset=utf-8".toMediaType())
                
                Log.d(TAG, "Sending JSON: ${payload.take(100)}")
                
                val builder = Request.Builder()
                    .url(serverUrl)
                    .post(requestBody)
                
                if (!authToken.isNullOrEmpty()) {
                    builder.addHeader("Authorization", "Bearer $authToken")
                }
                
                val request = builder.build()
                
                client.newCall(request).execute().use { response ->
                    Log.d(TAG, "Response code: ${response.code}")
                    val responseBody = response.body?.string()
                    Log.d(TAG, "Response body: $responseBody")
                    
                    if (response.isSuccessful) {
                        if (attempt > 1) {
                            Log.i(TAG, "Success after $attempt attempts")
                        }
                        return true
                    } else {
                        Log.w(TAG, "Server returned error: ${response.code}")
                        lastException = Exception("HTTP ${response.code}")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error sending notification (attempt $attempt): ${e.message}", e)
                lastException = e
            }
        }
        
        Log.e(TAG, "Failed after $maxRetries attempts. Last error: ${lastException?.message}")
        return false
    }
    
    private fun isValidUrl(urlString: String): Boolean {
        return try {
            val url = URL(urlString)
            // Only allow HTTP/HTTPS
            if (url.protocol != "http" && url.protocol != "https") {
                return false
            }
            // Security: Only allow local network for safety
            isLocalNetwork(urlString)
        } catch (e: Exception) {
            false
        }
    }
    
    private fun isLocalNetwork(urlString: String): Boolean {
        return try {
            val url = URL(urlString)
            val host = url.host
            
            Log.d(TAG, "Checking if local network: $host")
            
            // Cho phép localhost và IP local
            val isLocal = host == "localhost" || 
            host == "127.0.0.1" ||
            host.startsWith("192.168.") ||
            host.startsWith("10.") ||
            host.startsWith("172.16.") ||
            host.startsWith("172.17.") ||
            host.startsWith("172.18.") ||
            host.startsWith("172.19.") ||
            host.startsWith("172.20.") ||
            host.startsWith("172.21.") ||
            host.startsWith("172.22.") ||
            host.startsWith("172.23.") ||
            host.startsWith("172.24.") ||
            host.startsWith("172.25.") ||
            host.startsWith("172.26.") ||
            host.startsWith("172.27.") ||
            host.startsWith("172.28.") ||
            host.startsWith("172.29.") ||
            host.startsWith("172.30.") ||
            host.startsWith("172.31.")
            
            Log.d(TAG, "Is local network: $isLocal")
            isLocal
        } catch (e: Exception) {
            Log.e(TAG, "Error checking local network", e)
            false
        }
    }
    
    private fun sanitizeContent(content: String): String {
        // Giới hạn độ dài để tránh DoS
        val maxLength = 2000
        val truncated = if (content.length > maxLength) {
            content.substring(0, maxLength) + "..."
        } else {
            content
        }
        
        // Loại bỏ các ký tự điều khiển nguy hiểm
        return truncated.replace(Regex("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]"), "")
    }
    
    /**
     * GET request to server
     */
    fun get(url: String, authToken: String? = null): String? {
        return try {
            if (!isValidUrl(url)) {
                Log.w(TAG, "Invalid URL: $url")
                return null
            }
            
            val builder = Request.Builder()
                .url(url)
                .get()
            
            if (!authToken.isNullOrEmpty()) {
                builder.addHeader("Authorization", "Bearer $authToken")
            }
            
            val request = builder.build()
            
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    response.body?.string()
                } else {
                    Log.w(TAG, "GET failed: ${response.code}")
                    null
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "GET error: ${e.message}", e)
            null
        }
    }
    
    /**
     * POST JSON to server
     */
    fun postJson(url: String, json: String, authToken: String? = null): Boolean {
        return try {
            if (!isValidUrl(url)) {
                Log.w(TAG, "Invalid URL: $url")
                return false
            }
            
            val requestBody = json.toRequestBody("application/json; charset=utf-8".toMediaType())
            
            val builder = Request.Builder()
                .url(url)
                .post(requestBody)
            
            if (!authToken.isNullOrEmpty()) {
                builder.addHeader("Authorization", "Bearer $authToken")
            }
            
            val request = builder.build()
            
            client.newCall(request).execute().use { response ->
                response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e(TAG, "POST error: ${e.message}", e)
            false
        }
    }
}
