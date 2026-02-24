package com.banknotifier

import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * Shared thread pool to avoid creating unbounded raw Threads.
 * - networkIO: 2-thread pool for HTTP calls (notification sending, connection checks)
 * - diskIO: single thread for disk-bound work (app list loading, etc.)
 */
object AppExecutors {
    val networkIO: ExecutorService = Executors.newFixedThreadPool(2)
    val diskIO: ExecutorService = Executors.newSingleThreadExecutor()
}
