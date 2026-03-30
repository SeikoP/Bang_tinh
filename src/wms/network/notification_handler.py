"""
Notification Handler - HTTP request handler for Android notifications
"""

import json
import time
import threading
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ..core.constants import ALL_BANK_PACKAGES
from ..database.connection import get_connection


class NotificationHandler(BaseHTTPRequestHandler):
    """Server xử lý thông báo từ app Android - Filter tại PC"""

    # Bank packages imported from centralized constants
    BANK_PACKAGES = ALL_BANK_PACKAGES

    # Rate limiting: IP -> [timestamp, count]
    _rate_limit_store = {}
    _rate_limit_lock = threading.Lock()
    RATE_LIMIT_Window = 60  # seconds
    RATE_LIMIT_MAX = 100    # requests per window

    def _get_rate_limit_params(self):
        """Get rate limit parameters, allowing overrides from server instance"""
        window = getattr(self.server, "rate_limit_window", self.RATE_LIMIT_Window)
        max_reqs = getattr(self.server, "rate_limit_max", self.RATE_LIMIT_MAX)
        return window, max_reqs

    def _check_rate_limit(self, ip_address):
        """Simple token bucket rate limiting with thread safety"""
        time_now = time.time()
        window, max_reqs = self._get_rate_limit_params()
        
        with self._rate_limit_lock:
            # Initialize or reset if window expired
            if ip_address not in self._rate_limit_store:
                self._rate_limit_store[ip_address] = [time_now, 1]
                return True
            
            start_time, count = self._rate_limit_store[ip_address]
            
            if time_now - start_time > window:
                # Reset window
                self._rate_limit_store[ip_address] = [time_now, 1]
                return True
            
            if count >= max_reqs:
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.warning(f"Rate limit exceeded for {ip_address}")
                return False
                
            self._rate_limit_store[ip_address][1] += 1
            return True

    def handle_request(self):
        """Handle incoming notification request"""
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

            # Process message BEFORE sending response to ensure it's handled
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
                        # Send response for filtered notification
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"status":"success","message":"filtered"}')
                        return

                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info(
                            f"Accepted notification from: {package_name}"
                        )

                # Đẩy lên giao diện TRƯỚC KHI gửi response
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(
                        f"Processing notification: {content[:100]}..."
                    )
                if getattr(self.server, "signal", None):
                    self.server.signal.emit(str(content))
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info("Signal emitted successfully")
                
                # Gửi response SAU KHI đã xử lý
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"success","message":"received"}')
            else:
                # No content found
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
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
        # Check rate limit first for ALL requests
        if not self._check_rate_limit(self.client_address[0]):
            self.send_error(429, "Too Many Requests")
            return

        if self.path.startswith("/api/session"):
            self.handle_get_session()
        elif self.path.startswith("/api/notes"):
            self.handle_get_notes()
        else:
            self.handle_request()  # Default notification handling

    def do_POST(self):
        """Handle POST requests"""
        # Check rate limit first for ALL requests
        if not self._check_rate_limit(self.client_address[0]):
            self.send_error(429, "Too Many Requests")
            return

        if self.path.startswith("/api/session"):
            self.handle_post_session()
        elif self.path.startswith("/api/notes"):
            self.handle_post_notes()
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
            action = payload.get("action", "update")  # "handover", "close_shift", or "update"
            notes = payload.get("notes", "")
            shift_name = (payload.get("shift_name") or "").strip()

            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"POST /api/session - action: {action}, updates: {len(updates)}")

            container = getattr(self.server, "container", None)
            if not container:
                raise Exception("Container not found")

            repo = container.get("session_repo")
            if not repo:
                raise Exception("Session repository not found")

            history_repo = container.get("history_repo")

            # Get current state to verify handover quantities
            current_sessions = {s.product.id: s for s in repo.get_all()}

            def apply_updates(update_list):
                with get_connection() as conn:
                    cursor = conn.cursor()
                    for update in update_list:
                        pid = update.get("product_id")
                        if pid not in current_sessions:
                            continue

                        current = current_sessions[pid]
                        handover = update.get("handover_qty", current.handover_qty)
                        closing = update.get("closing_qty", current.closing_qty)
                        # Validate
                        if handover < 0:
                            handover = 0
                        if closing < 0:
                            closing = 0
                        if closing > handover:
                            closing = handover
                        cursor.execute(
                            """INSERT OR REPLACE INTO session_data (product_id, handover_qty, closing_qty)
                               VALUES (?, ?, ?)""",
                            (pid, handover, closing),
                        )
                        current.handover_qty = handover
                        current.closing_qty = closing

            if action == "handover":
                # Save current session history BEFORE applying handover
                if history_repo:
                    try:
                        apply_updates(updates)
                        history_repo.save_current_session(
                            shift_name or "Giao ca (Android)", notes
                        )
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.info(
                                f"Handover: Saved history as '{shift_name or 'Giao ca (Android)'}'"
                            )
                    except Exception as hist_err:
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.warning(f"Failed to save history before handover: {hist_err}")

                # Giao ca: closing_qty becomes new handover_qty, reset closing to 0
                with get_connection() as conn:
                    cursor = conn.cursor()
                    for update in updates:
                        pid = update.get("product_id")
                        if pid not in current_sessions:
                            continue

                        current = current_sessions[pid]
                        closing = update.get("closing_qty", current.closing_qty)

                        # New handover = current closing (what's left for next shift)
                        cursor.execute(
                            """INSERT OR REPLACE INTO session_data (product_id, handover_qty, closing_qty)
                               VALUES (?, ?, ?)""",
                            (pid, closing, 0),
                        )
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.info(f"Handover: Product {pid} - new handover={closing}, closing=0")

            elif action == "close_shift":
                apply_updates(updates)
                if history_repo:
                    try:
                        history_repo.save_current_session(
                            shift_name or "Chốt ca (Android)", notes
                        )
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.info(
                                f"Close shift: Saved history as '{shift_name or 'Chốt ca (Android)'}'"
                            )
                    except Exception as hist_err:
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.warning(f"Failed to save history for close shift: {hist_err}")

            else:
                apply_updates(updates)

            # Emit signal to refresh UI
            if hasattr(self.server, "signal"):
                # Use special command format for system actions
                msg = json.dumps(
                    {
                        "has_command": True,
                        "command": "REFRESH_SESSION",
                        "content": f"Remote Update: {action}",
                        "notes": notes,
                    }
                )
                self.server.signal.emit(msg)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "action": action}).encode("utf-8"))

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"API Error (POST session): {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"success": False, "error": str(e)}).encode("utf-8")
            )

    def handle_get_notes(self):
        """API: Get notes/tasks"""
        try:
            if not self._check_auth():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Unauthorized"}).encode("utf-8"))
                return

            container = getattr(self.server, "container", None)
            if not container:
                raise Exception("Container not found")

            task_repo = container.get("task_repo")
            if not task_repo:
                raise Exception("Task repository not found")

            tasks = task_repo.get_all()
            data = []
            for t in tasks:
                data.append({
                    "id": t.id,
                    "task_type": t.task_type,
                    "description": t.description,
                    "customer_name": t.customer_name,
                    "amount": float(t.amount),
                    "created_at": t.created_at,
                    "completed": t.completed,
                    "notes": t.notes,
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "notes": data}).encode("utf-8"))

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"API Error (GET notes): {e}", exc_info=True)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

    def handle_post_notes(self):
        """API: Add or update a note/task"""
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

            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"POST /api/notes - payload: {str(payload)[:200]}")

            container = getattr(self.server, "container", None)
            if not container:
                raise Exception("Container not found")

            task_repo = container.get("task_repo")
            if not task_repo:
                raise Exception("Task repository not found")

            action = payload.get("action", "add")

            if action == "add":
                task_id = task_repo.add(
                    task_type=payload.get("task_type", "note"),
                    description=payload.get("description", ""),
                    customer_name=payload.get("customer_name", ""),
                    amount=float(payload.get("amount", 0)),
                    notes=payload.get("notes", ""),
                )
                result = {"success": True, "action": "add", "id": task_id}
            elif action == "update":
                task_id = payload.get("id")
                if not task_id:
                    raise Exception("Missing task id")
                task_repo.update(
                    task_id=task_id,
                    task_type=payload.get("task_type", "note"),
                    description=payload.get("description", ""),
                    customer_name=payload.get("customer_name", ""),
                    amount=float(payload.get("amount", 0)),
                    notes=payload.get("notes", ""),
                )
                result = {"success": True, "action": "update", "id": task_id}
            elif action == "complete":
                task_id = payload.get("id")
                if not task_id:
                    raise Exception("Missing task id")
                task_repo.mark_completed(task_id)
                result = {"success": True, "action": "complete", "id": task_id}
            elif action == "delete":
                task_id = payload.get("id")
                if not task_id:
                    raise Exception("Missing task id")
                task_repo.delete(task_id)
                result = {"success": True, "action": "delete", "id": task_id}
            else:
                raise Exception(f"Unknown action: {action}")

            # Emit signal to refresh UI
            if hasattr(self.server, "signal"):
                msg = json.dumps({
                    "has_command": True,
                    "command": "REFRESH_TASKS",
                    "content": f"Remote Note: {action}",
                })
                self.server.signal.emit(msg)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"API Error (POST notes): {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        # Silent logging - use server logger instead
        return
