package com.banknotifier

data class NotificationItem(
    val id: Long,
    val content: String,
    val packageName: String,
    val timestamp: Long,
    val success: Boolean,
    val errorMessage: String? = null
)
