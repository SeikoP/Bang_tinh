"""
Notification Handler - HTTP request handler for Android notifications
"""

import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from core.constants import ALL_BANK_PACKAGES


class NotificationHandler(BaseHTTPRequestHandler):
    """Server xử lý thông báo từ app Android - Filter tại PC"""

    # Bank packages imported from centralized constants
    BANK_PACKAGES = ALL_BANK_PACKAGES

    # Rate limiting: IP -> [timestamp, count]
    _rate_limit_store = {}
    RATE_LIMIT_Window = 60  # seconds
    RATE_LIMIT_MAX = 100    # requests per window

    def _check_rate_limit(self, ip_address):
        """Simple token bucket rate limiting"""
        time_now = time.time()
        
        # Initialize or reset if window expired
        if ip_address not in self._rate_limit_store:
            self._rate_limit_store[ip_address] = [time_now, 1]
            return True
        
        start_time, count = self._rate_limit_store[ip_address]
        
        if time_now - start_time > self.RATE_LIMIT_Window:
            # Reset window
            self._rate_limit_store[ip_address] = [time_now, 1]
            return True
        
        if count >= self.RATE_LIMIT_MAX:
            return False
            
        self._rate_limit_store[ip_address][1] += 1
        return True

    def handle_request(self):
        # Check rate limit
        if not self._check_rate_limit(self.client_address[0]):
            self.send_error(429, "Too Many Requests")
            return


        try:
            msg = None
            # Log incoming request
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(
                    f"=== Received {self.command} request to {self.path} ==="
                )
                self.server.logger.info(f"Headers: {dict(self.headers)}")

            # --- SECURITY CHECK ---
            auth_header = self.headers.get("Authorization")
            expected_key = getattr(self.server, "secret_key", None)

            # If server has a secret key configured, enforce it
            if expected_key:
                if not auth_header or not auth_header.startswith("Bearer "):
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        b'{"status":"error","message":"Unauthorized: Missing or invalid token"}'
                    )
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.warning(
                            f"Unauthorized request from {self.client_address}"
                        )
                    return

                token = auth_header.split(" ")[1].strip()
                if token != expected_key:
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        b'{"status":"error","message":"Forbidden: Invalid token"}'
                    )
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.warning(
                            f"Forbidden request from {self.client_address}: Invalid token"
                        )
                    return
            # ----------------------

            # 1. Thử lấy từ URL Query (?content=...)
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"Query params: {query_params}")

            if "content" in query_params:
                msg = query_params["content"][0]
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(f"Found content in query: {msg}")

            # 2. Nếu URL không có, thử lấy từ Body
            if not msg:
                content_length = self.headers.get("Content-Length")
                content_type = self.headers.get("Content-Type", "")
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(
                        f"Content-Length: {content_length}, Content-Type: {content_type}"
                    )

                if content_length and int(content_length) > 0:
                    post_data = self.rfile.read(int(content_length)).decode("utf-8")
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info(f"Received body: {post_data}")

                    # Try JSON first
                    try:
                        data = json.loads(post_data)
                        msg = data.get("content", post_data)
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.info(f"Parsed JSON, content: {msg}")
                    except json.JSONDecodeError:
                        # Try form data (application/x-www-form-urlencoded)
                        if "application/x-www-form-urlencoded" in content_type:
                            form_params = parse_qs(post_data)
                            if "content" in form_params:
                                msg = form_params["content"][0]
                                if (
                                    hasattr(self.server, "logger")
                                    and self.server.logger
                                ):
                                    self.server.logger.info(
                                        f"Parsed form data, content: {msg}"
                                    )
                            else:
                                msg = post_data
                        else:
                            msg = post_data
                            if hasattr(self.server, "logger") and self.server.logger:
                                self.server.logger.info(
                                    f"Not JSON/form, using raw body: {msg}"
                                )

            # Luôn phản hồi success để Android biết đã nhận
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if msg:
                # Try to parse as JSON to get package info
                package_name = None
                content = msg
                try:
                    data = json.loads(msg)
                    if isinstance(data, dict):
                        package_name = data.get("package")
                        # Get content - might be nested JSON string
                        raw_content = data.get("content", msg)

                        # Only try to parse content if it looks like JSON (starts with { or [)
                        if isinstance(
                            raw_content, str
                        ) and raw_content.strip().startswith(("{", "[")):
                            try:
                                content_data = json.loads(raw_content)
                                if isinstance(content_data, dict):
                                    # Extract actual content from nested structure
                                    content = content_data.get("content", raw_content)
                                else:
                                    content = raw_content
                            except (json.JSONDecodeError, TypeError):
                                content = raw_content
                        else:
                            content = raw_content
                except (json.JSONDecodeError, TypeError):
                    pass

                # Filter by package name (PC-side filtering)
                if package_name:
                    if package_name not in self.BANK_PACKAGES:
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.debug(
                                f"Filtered out notification from: {package_name}"
                            )
                        self.wfile.write(b'{"status":"success","message":"filtered"}')
                        return

                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info(
                            f"Accepted notification from: {package_name}"
                        )

                self.wfile.write(b'{"status":"success","message":"received"}')
                # Đẩy lên giao diện
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(
                        f"Processing notification: {content[:100]}..."
                    )
                if hasattr(self.server, "signal"):
                    self.server.signal.emit(str(content))
            else:
                self.wfile.write(b'{"status":"success","message":"no content found"}')
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.warning("No content found in request")

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"Error handling request: {e}", exc_info=True)
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(f'{{"status":"error","message":"{str(e)}"}}'.encode())
            except:
                pass

    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith("/api/session"):
            self.handle_get_session()
        else:
            self.handle_request()  # Default notification handling

    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith("/api/session"):
            self.handle_post_session()
        else:
            self.handle_request()

    def _check_auth(self):
        """Helper to enforce auth"""
        auth_header = self.headers.get("Authorization")
        expected_key = getattr(self.server, "secret_key", None)

        if expected_key:
            if not auth_header or not auth_header.startswith("Bearer "):
                return False
            token = auth_header.split(" ")[1].strip()
            if token != expected_key:
                return False
        return True

    def handle_get_session(self):
        """API: Get current session data"""
        try:
            # Log request
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"GET /api/session from {self.client_address}")

            # Check auth
            if not self._check_auth():
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.warning("Auth failed for /api/session")
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"success": False, "error": "Unauthorized"}).encode(
                        "utf-8"
                    )
                )
                return

            container = getattr(self.server, "container", None)
            if not container:
                raise Exception("Container not found in server context")

            repo = container.get("session_repo")
            if not repo:
                raise Exception("Session repository not found")

            sessions = repo.get_all()
            data = []
            for s in sessions:
                data.append(
                    {
                        "product_id": s.product.id,
                        "product_name": s.product.name,
                        "large_unit": s.product.large_unit,
                        "conversion": s.product.conversion,
                        "unit_price": float(s.product.unit_price),
                        "unit_char": s.product.unit_char,
                        "handover_qty": s.handover_qty,
                        "closing_qty": s.closing_qty,
                        "used_qty": s.used_qty,
                        "amount": float(s.amount),
                    }
                )

            response = {"success": True, "session": data}

            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"Returning {len(data)} session items")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"API Error (GET session): {e}", exc_info=True)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"success": False, "error": str(e)}).encode("utf-8")
            )

    def handle_post_session(self):
        """API: Update session data"""
        if not self._check_auth():
            self.send_response(401)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                raise Exception("Empty body")

            post_data = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(post_data)
            updates = payload.get("updates", [])

            container = getattr(self.server, "container", None)
            if not container:
                raise Exception("Container not found")

            repo = container.get("session_repository")
            if not repo:
                raise Exception("Session repository not found")

            # Get current state to verify handover quantities
            current_sessions = {s.product.id: s for s in repo.get_all()}

            for update in updates:
                pid = update.get("product_id")
                closing = update.get("closing_qty")

                if pid in current_sessions:
                    current = current_sessions[pid]
                    # Update closing quantity, keep handover same
                    repo.update_qty(pid, current.handover_qty, closing)

            # Emit signal to refresh UI
            if hasattr(self.server, "signal"):
                # Use special command format for system actions
                msg = json.dumps(
                    {
                        "has_command": True,
                        "command": "REFRESH_SESSION",
                        "content": "Remote Update",
                    }
                )
                self.server.signal.emit(msg)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"API Error (POST session): {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"success": False, "error": str(e)}).encode("utf-8")
            )

    def log_message(self, format, *args):
        # Silent logging - use server logger instead
        return
