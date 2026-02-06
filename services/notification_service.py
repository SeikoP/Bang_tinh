"""
Notification Service - HTTP server for receiving bank notifications with security
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from typing import Callable, Dict, Optional
from urllib.parse import parse_qs, urlparse

from core.exceptions import AppException, ValidationError


class RateLimiter:
    """Simple rate limiter to prevent abuse"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request from client is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)

            # Clean old requests
            self._requests[client_ip] = [
                req_time for req_time in self._requests[client_ip] if req_time > cutoff
            ]

            # Check limit
            if len(self._requests[client_ip]) >= self.max_requests:
                return False

            # Add current request
            self._requests[client_ip].append(now)
            return True


class NotificationRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler with validation and security"""

    def handle_request(self):
        """Handle incoming notification request with validation"""
        try:
            # Rate limiting
            client_ip = self.client_address[0]
            if hasattr(self.server, "rate_limiter"):
                if not self.server.rate_limiter.is_allowed(client_ip):
                    self.send_error(429, "Too Many Requests")
                    if hasattr(self.server, "logger"):
                        self.server.logger.warning(
                            f"Rate limit exceeded for {client_ip}"
                        )
                    return

            msg = None

            # Log incoming request
            if hasattr(self.server, "logger"):
                self.server.logger.debug(
                    f"Received {self.command} request from {client_ip}"
                )

            # 1. Try to get content from URL query (?content=...)
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            if "content" in query_params:
                msg = query_params["content"][0]

            # 2. If not in URL, try to get from request body
            if not msg:
                content_length = self.headers.get("Content-Length")
                if content_length and int(content_length) > 0:
                    # Validate content length (prevent DoS)
                    if int(content_length) > 10240:  # 10KB max
                        self.send_error(413, "Payload Too Large")
                        return

                    post_data = self.rfile.read(int(content_length)).decode("utf-8")

                    # Validate Content-Type if present
                    content_type = self.headers.get("Content-Type", "")

                    if "application/json" in content_type:
                        try:
                            data = json.loads(post_data)

                            # Check if it's structured notification (with time, source, amount, content)
                            if isinstance(data, dict) and "content" in data:
                                # Pass the whole JSON object as string for parsing
                                msg = json.dumps(data, ensure_ascii=False)
                            else:
                                # Fallback to content field only
                                msg = data.get("content", "")
                                if not isinstance(msg, str):
                                    self.send_error(400, "Invalid content format")
                                    return
                        except json.JSONDecodeError:
                            self.send_error(400, "Invalid JSON")
                            return
                    else:
                        # Plain text content
                        msg = post_data

            # Validate message content
            if msg:
                # Sanitize message (basic XSS prevention)
                msg = self._sanitize_message(msg)

                # Validate message length
                if len(msg) > 1000:  # Max 1000 characters
                    msg = msg[:1000]

                # Send response first
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"success"}')

                # Process message
                if (
                    hasattr(self.server, "message_handler")
                    and self.server.message_handler
                ):
                    try:
                        self.server.message_handler(str(msg))
                    except Exception as handler_error:
                        if hasattr(self.server, "logger"):
                            self.server.logger.error(
                                f"Error in message handler: {handler_error}"
                            )
                else:
                    if hasattr(self.server, "logger"):
                        self.server.logger.warning("No message handler registered!")

                if hasattr(self.server, "logger"):
                    # Safe logging with ASCII encoding to avoid Unicode errors
                    safe_msg = msg[:50].encode("ascii", "replace").decode("ascii")
                    self.server.logger.info(f"Notification received: {safe_msg}...")
            else:
                self.send_error(400, "Missing content parameter")

        except Exception as e:
            if hasattr(self.server, "logger"):
                self.server.logger.error(f"Error handling request: {e}")
            try:
                self.send_error(500, "Internal Server Error")
            except:
                pass

    def _sanitize_message(self, message: str) -> str:
        """
        Sanitize message content to prevent XSS.

        Args:
            message: Raw message content

        Returns:
            Sanitized message
        """
        # Check if message is JSON - if so, don't sanitize (it's structured data)
        try:
            json.loads(message)
            # Valid JSON, return as-is
            return message
        except (json.JSONDecodeError, TypeError):
            # Not JSON, sanitize plain text
            # Remove potentially dangerous characters for HTML display
            dangerous_chars = ["<", ">"]
            sanitized = message
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")
            return sanitized

    def do_POST(self):
        """Handle POST requests"""
        self.handle_request()

    def do_GET(self):
        """Handle GET requests"""
        self.handle_request()

    def log_message(self, format, *args):
        """Override to use custom logger"""
        if hasattr(self.server, "logger"):
            self.server.logger.debug(format % args)


class NotificationService:
    """
    Service for receiving and processing bank notifications via HTTP.
    Implements security features: request validation, rate limiting, input sanitization.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5005,
        logger: Optional[logging.Logger] = None,
        max_requests_per_minute: int = 100,
    ):
        """
        Initialize notification service.

        Args:
            host: Server host address
            port: Server port
            logger: Logger instance
            max_requests_per_minute: Rate limit threshold
        """
        self.host = host
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[Thread] = None
        self._message_handler: Optional[Callable] = None
        self._running = False
        self.rate_limiter = RateLimiter(
            max_requests=max_requests_per_minute, window_seconds=60
        )

        self.logger.info(f"NotificationService initialized on {host}:{port}")

    def register_handler(self, handler: Callable[[str], None]) -> None:
        """
        Register callback handler for received messages.

        Args:
            handler: Callback function that takes message string as parameter
        """
        if not callable(handler):
            raise ValidationError("Handler must be callable", "handler")

        self._message_handler = handler
        self.logger.info("Message handler registered")

    def start_server(self) -> None:
        """
        Start the notification server in a background thread.

        Raises:
            AppException: If server fails to start
        """
        if self._running:
            self.logger.warning("Server already running")
            return

        try:
            self.server = ThreadingHTTPServer(
                (self.host, self.port), NotificationRequestHandler
            )
            self.server.allow_reuse_address = True
            self.server.timeout = 5

            # Attach dependencies to server
            self.server.message_handler = self._message_handler
            self.server.logger = self.logger
            self.server.rate_limiter = self.rate_limiter

            # Start server in background thread
            self.server_thread = Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            self._running = True
            self.logger.info(f"Notification server started on {self.host}:{self.port}")

        except OSError as e:
            self.logger.error(f"Failed to start notification server: {e}")
            raise AppException(
                f"Cannot start notification server on port {self.port}",
                "SERVER_START_ERROR",
                {"host": self.host, "port": self.port, "error": str(e)},
            ) from e

    def stop_server(self) -> None:
        """Stop the notification server."""
        if not self._running:
            self.logger.warning("Server not running")
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()

            if self.server_thread:
                self.server_thread.join(timeout=5)

            self._running = False
            self.logger.info("Notification server stopped")

        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            raise AppException(
                "Failed to stop notification server",
                "SERVER_STOP_ERROR",
                {"error": str(e)},
            ) from e

    def _run_server(self):
        """Internal method to run server loop."""
        try:
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self._running = False

    def is_running(self) -> bool:
        """
        Check if server is running.

        Returns:
            True if running, False otherwise
        """
        return self._running
