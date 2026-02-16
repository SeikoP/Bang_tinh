"""
Database Connection Pool
Reuse connections instead of creating new ones
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Queue
from typing import Generator, Optional


class ConnectionPool:
    """
    SQLite connection pool

    Features:
    - Connection reuse
    - Thread-safe
    - Automatic cleanup
    - Health checks

    Usage:
        pool = ConnectionPool(db_path, pool_size=5)

        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
    """

    # Health check threshold - only check if idle longer than this (seconds)
    HEALTH_CHECK_IDLE_THRESHOLD = 60.0

    def __init__(
        self,
        db_path: Path,
        pool_size: int = 5,
        timeout: float = 30.0,
        max_idle_time: float = 300.0,  # 5 minutes
    ):
        """
        Initialize connection pool with lazy initialization.
        Connections are created on demand, not upfront.

        Args:
            db_path: Path to database file
            pool_size: Maximum number of connections
            timeout: Timeout for getting connection (seconds)
            max_idle_time: Maximum idle time before closing connection (seconds)
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.max_idle_time = max_idle_time

        # Connection pool (queue of (connection, last_used_time))
        self._pool: Queue = Queue(maxsize=pool_size)

        # Lock for thread safety
        self._lock = threading.Lock()

        # Statistics
        self._created_connections = 0
        self._active_connections = 0
        self._total_requests = 0
        self._total_waits = 0

        # Lazy init: only create 1 connection upfront for immediate availability
        conn = self._create_connection()
        self._pool.put((conn, time.time()))

    def _create_connection(self) -> sqlite3.Connection:
        """Create new database connection"""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Allow use in multiple threads
            timeout=self.timeout,
        )
        conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")

        with self._lock:
            self._created_connections += 1

        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get connection from pool

        Yields:
            Database connection

        Raises:
            Empty: If no connection available within timeout
        """
        conn = None
        start_time = time.time()

        try:
            # Get connection from pool
            try:
                conn, last_used = self._pool.get(timeout=self.timeout)

                with self._lock:
                    self._total_requests += 1
                    self._active_connections += 1
                    if time.time() - start_time > 0.1:
                        self._total_waits += 1

                idle_time = time.time() - last_used

                # Check if connection is stale
                if idle_time > self.max_idle_time:
                    # Close stale connection and create new one
                    try:
                        conn.close()
                    except:
                        pass
                    conn = self._create_connection()
                elif idle_time > self.HEALTH_CHECK_IDLE_THRESHOLD:
                    # Only health check if idle > threshold (skip for fresh connections)
                    try:
                        conn.execute("SELECT 1")
                    except sqlite3.Error:
                        try:
                            conn.close()
                        except:
                            pass
                        conn = self._create_connection()

                yield conn
                conn.commit()

            except Empty:
                # No connection available, create new one (lazy growth)
                conn = self._create_connection()

                with self._lock:
                    self._total_requests += 1
                    self._total_waits += 1

                yield conn
                conn.commit()

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise e

        finally:
            # Return connection to pool
            if conn:
                try:
                    # Put back in pool if pool not full
                    self._pool.put_nowait((conn, time.time()))
                except:
                    # Pool is full, close connection
                    try:
                        conn.close()
                    except:
                        pass

                with self._lock:
                    self._active_connections -= 1

    def close_all(self):
        """Close all connections in pool"""
        while not self._pool.empty():
            try:
                conn, _ = self._pool.get_nowait()
                conn.close()
            except:
                pass

    def get_stats(self) -> dict:
        """Get pool statistics"""
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "available": self._pool.qsize(),
                "active": self._active_connections,
                "created": self._created_connections,
                "total_requests": self._total_requests,
                "total_waits": self._total_waits,
                "wait_ratio": self._total_waits / max(self._total_requests, 1),
            }


# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def initialize_pool(db_path: Path, pool_size: int = 5):
    """Initialize global connection pool"""
    global _connection_pool

    with _pool_lock:
        if _connection_pool is None:
            _connection_pool = ConnectionPool(db_path, pool_size)


def get_pooled_connection():
    """Get connection from global pool"""

    if _connection_pool is None:
        raise RuntimeError(
            "Connection pool not initialized. Call initialize_pool() first."
        )

    return _connection_pool.get_connection()


def close_pool():
    """Close global connection pool"""
    global _connection_pool

    with _pool_lock:
        if _connection_pool:
            _connection_pool.close_all()
            _connection_pool = None


def get_pool_stats() -> dict:
    """Get global pool statistics"""

    if _connection_pool:
        return _connection_pool.get_stats()
    return {}
