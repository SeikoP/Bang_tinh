"""
Notification Service - HTTP server for receiving bank notifications with security
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from typing import Callable, Dict, Optional
from urllib.parse import parse_qs, urlparse

from ..core.exceptions import AppException, ValidationError


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


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
        """Handle incoming notification request with validation and authentication"""
        try:
            # 1. Rate limiting
            client_ip = self.client_address[0]
            if hasattr(self.server, "rate_limiter"):
                if not self.server.rate_limiter.is_allowed(client_ip):
                    self.send_error(429, "Too Many Requests")
                    if hasattr(self.server, "logger"):
                        self.server.logger.warning(
                            f"Rate limit exceeded for {client_ip}"
                        )
                    return

            # 2. Authentication Check (Crucial for security)
            # All API calls and notifications require the correct secret_key
            expected_key = None
            if hasattr(self.server, "container") and self.server.container:
                config = self.server.container.get("config")
                if config:
                    expected_key = config.secret_key

            parsed_url = urlparse(self.path)

            # Log every incoming request for debugging Android connectivity
            if hasattr(self.server, "logger"):
                self.server.logger.info(
                    f"[REQ] {self.command} {self.path} from {client_ip} "
                    f"Auth={self.headers.get('Authorization', '(none)')!r} "
                    f"CT={self.headers.get('Content-Type', '(none)')}"
                )

            # Allow unauthenticated GET probes only (Cloudflare tunnel health checks)
            # POST requests MUST still authenticate — Android Ping should prove auth works.
            if self.command == "GET" and parsed_url.path in ("/", "/health", "/favicon.ico"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok","auth":"not_checked"}')
                return

            # --- Extract auth key from multiple sources ---
            # Source 1: Authorization: Bearer <key>
            auth_header = self.headers.get("Authorization", "")
            provided_key = ""
            if auth_header.startswith("Bearer "):
                provided_key = auth_header[7:].strip()

            # Source 2: ?key=<key> query parameter
            if not provided_key:
                query_params = parse_qs(parsed_url.query)
                if "key" in query_params:
                    provided_key = query_params["key"][0]

            # Source 3: Peek into JSON body for "key" field (Android fallback)
            # This handles the case where Android sends key in the payload
            _peeked_body = None
            if not provided_key and self.command == "POST":
                try:
                    content_length = self.headers.get("Content-Length")
                    transfer_encoding = self.headers.get("Transfer-Encoding", "").lower()
                    if content_length and int(content_length) > 0 and int(content_length) <= 10240:
                        _peeked_body = self.rfile.read(int(content_length))
                        body_data = json.loads(_peeked_body.decode("utf-8", errors="replace"))
                        if isinstance(body_data, dict) and "key" in body_data:
                            provided_key = str(body_data["key"]).strip()
                except Exception:
                    pass

            # Log full debug info for auth failures
            if expected_key and provided_key != expected_key:
                if hasattr(self.server, "logger"):
                    auth_dbg = (
                        f"Unauthorized from {client_ip} path={parsed_url.path} "
                        f"method={self.command} has_key={'yes' if provided_key else 'no'} "
                        f"auth_header={'[Bearer ...]' if auth_header.startswith('Bearer ') else repr(auth_header)} "
                        f"content_type={self.headers.get('Content-Type', 'none')}"
                    )
                    self.server.logger.warning(auth_dbg)
                self.send_error(401, "Unauthorized - Invalid API Key")
                return

            # If we peeked the body for auth, store it so handle_request can reuse it
            self._peeked_body = _peeked_body

            # --- AUTHENTICATED ACCESS GRANTED ---

            # --- REMOTE SESSION API ---

            # GET /api/ping - Real connectivity check
            if self.command == "GET" and parsed_url.path == "/api/ping":
                checks = {"server": True, "auth": True, "database": False, "signal": False}
                errors = []
                try:
                    from ..database.repositories import SessionRepository
                    SessionRepository.get_all()
                    checks["database"] = True
                except Exception as e:
                    errors.append(f"database: {e}")
                if getattr(self.server, "message_handler", None) is not None:
                    checks["signal"] = True
                else:
                    errors.append("signal: message_handler not connected — notifications won't reach desktop")
                all_ok = all(checks.values())
                result = {
                    "status": "ok" if all_ok else "degraded",
                    "checks": checks,
                    "ready": all_ok,
                }
                if errors:
                    result["errors"] = errors
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
                return

            # GET /api/session - Get current session data
            if self.command == "GET" and parsed_url.path == "/api/session":
                try:
                    from ..database.repositories import SessionRepository

                    sessions = SessionRepository.get_all()

                    data = {
                        "success": True,
                        "total_amount": float(sum(s.amount for s in sessions)),
                        "session": [
                            {
                                "product_id": s.product.id,
                                "product_name": s.product.name,
                                "large_unit": s.product.large_unit,
                                "conversion": s.product.conversion,
                                "unit_price": float(s.product.unit_price),
                                "unit_char": s.product.unit_char
                                or ("t" if s.product.conversion > 1 else ""),
                                "handover_qty": s.handover_qty,
                                "closing_qty": s.closing_qty,
                                "used_qty": s.used_qty,
                                "amount": float(s.amount),
                            }
                            for s in sessions
                        ],
                    }

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(data, ensure_ascii=False, cls=DecimalEncoder).encode(
                            "utf-8"
                        )
                    )
                    return
                except Exception as e:
                    self.send_error(500, f"Error getting session: {str(e)}")
                    return

            # POST /api/session - Update closing quantities
            if self.command == "POST" and parsed_url.path == "/api/session":
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    if content_length == 0:
                        self.send_error(400, "Missing body")
                        return

                    post_data = self.rfile.read(content_length).decode("utf-8")
                    update_data = json.loads(post_data)

                    if "updates" not in update_data:
                        self.send_error(400, "Missing 'updates' in payload")
                        return

                    from ..database.repositories import SessionRepository

                    # Get current state to preserve handover_qty
                    current_sessions = {
                        s.product.id: s for s in SessionRepository.get_all()
                    }

                    success_count = 0
                    for update in update_data["updates"]:
                        pid = update.get("product_id")
                        closing = update.get("closing_qty")

                        if pid in current_sessions:
                            handover = current_sessions[pid].handover_qty
                            SessionRepository.update_qty(pid, handover, int(closing))
                            success_count += 1

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": True, "updated": success_count}).encode(
                            "utf-8"
                        )
                    )

                    # Notify desktop UI that session data has changed
                    if (
                        hasattr(self.server, "message_handler")
                        and self.server.message_handler
                    ):
                        try:
                            cmd_json = json.dumps(
                                {"command": "SESSION_UPDATED", "count": success_count}
                            )
                            self.server.message_handler(cmd_json)
                        except Exception as handler_err:
                            if hasattr(self.server, "logger"):
                                self.server.logger.error(
                                    f"Error notifying UI: {handler_err}"
                                )
                    return
                except Exception as e:
                    self.send_error(500, f"Error updating session: {str(e)}")
                    return

            # ─────────────────────────────────────────────────────────
            # CONFIG API  (used by Android to auto-refresh tunnel URL)
            # ─────────────────────────────────────────────────────────
            if self.command == "GET" and parsed_url.path == "/api/config":
                try:
                    from pathlib import Path as _Path
                    import hashlib as _hashlib
                    _tunnel_state = _Path(__file__).parents[2] / "config" / "tunnel_state.json"
                    _tunnel_url = ""
                    _tunnel_status = "down"
                    _tunnel_updated_at = 0
                    if _tunnel_state.exists():
                        try:
                            import json as _j
                            _state = _j.loads(
                                _tunnel_state.read_text(encoding="utf-8")
                            )
                            _tunnel_url = _state.get("tunnel_url", "")
                            _tunnel_status = _state.get("status", "up" if _tunnel_url else "down")
                            _tunnel_updated_at = int(_state.get("updated_at", 0) or 0)
                        except Exception:
                            pass
                    try:
                        from ..network.network_monitor import get_all_ips_flat, get_best_ip
                        _ips = get_all_ips_flat()
                        _best_ip, _best_type = get_best_ip()
                    except Exception:
                        _ips = []
                        _best_ip, _best_type = "127.0.0.1", "loopback"
                    _port = 5005
                    try:
                        _port = self.server.server_address[1]
                    except Exception:
                        pass

                    _version_input = json.dumps(
                        {
                            "tunnel_url": _tunnel_url,
                            "tunnel_status": _tunnel_status,
                            "ips": _ips,
                            "best_ip": _best_ip,
                            "port": _port,
                            "tunnel_updated_at": _tunnel_updated_at,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    _config_version = _hashlib.sha1(_version_input.encode("utf-8")).hexdigest()[:12]
                    _now_ts = int(datetime.now().timestamp())

                    body = json.dumps({
                        "success": True,
                        "tunnel_url": _tunnel_url,
                        "tunnel_status": _tunnel_status,
                        "tunnel_updated_at": _tunnel_updated_at,
                        "config_version": _config_version,
                        "config_expires_at": _now_ts + 300,
                        "primary_ip": _best_ip,
                        "primary_type": _best_type,
                        "ips": _ips,
                        "port": _port,
                    }, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # ─────────────────────────────────────────────────────────
            # NOTES / PAYMENT API
            # ─────────────────────────────────────────────────────────
            from ..database.task_repository import TaskRepository
            from ..database.task_models import Task
            import re as _re

            def _task_to_dict(task: Task) -> dict:
                return {
                    "id": task.id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "customer_name": task.customer_name,
                    "amount": task.amount,
                    "created_at": task.created_at.isoformat(),
                    "completed": task.completed,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "notes": task.notes,
                    "payment_status": task.payment_status,
                    "transfer_content": task.transfer_content,
                    "vietqr_url": task.vietqr_url,
                    "note_code": task.note_code,
                }

            def _load_bank_settings() -> dict:
                from pathlib import Path
                cfg_path = Path(__file__).parents[2] / "config" / "bank_settings.json"
                if cfg_path.exists():
                    try:
                        import json as _json
                        return _json.loads(cfg_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                return {}

            def _send_json(handler, data: dict, status: int = 200):
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                handler.send_response(status)
                handler.send_header("Content-Type", "application/json; charset=utf-8")
                handler.send_header("Content-Length", str(len(body)))
                handler.end_headers()
                handler.wfile.write(body)

            def _read_body(handler) -> bytes:
                content_length = handler.headers.get("Content-Length")
                transfer_encoding = handler.headers.get("Transfer-Encoding", "").lower()
                if content_length and int(content_length) > 0:
                    length = int(content_length)
                    if length > 102400:
                        raise ValueError("Payload too large")
                    return handler.rfile.read(length)
                if "chunked" in transfer_encoding:
                    chunks = []
                    total = 0
                    while True:
                        size_line = handler.rfile.readline().decode("utf-8", errors="replace").strip()
                        if not size_line:
                            break
                        chunk_size = int(size_line.split(";")[0], 16)
                        if chunk_size == 0:
                            break
                        if total + chunk_size > 102400:
                            raise ValueError("Payload too large")
                        chunks.append(handler.rfile.read(chunk_size))
                        total += chunk_size
                        handler.rfile.read(2)
                    return b"".join(chunks)
                return b""

            # GET /api/notes
            if self.command == "GET" and parsed_url.path == "/api/notes":
                try:
                    include_completed = parsed_url.query and "completed=1" in parsed_url.query
                    tasks = TaskRepository.get_all(include_completed=include_completed)
                    _send_json(self, {"success": True, "notes": [_task_to_dict(t) for t in tasks]})
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # GET /api/notes/pending-payments
            if self.command == "GET" and parsed_url.path == "/api/notes/pending-payments":
                try:
                    tasks = TaskRepository.find_pending_payments()
                    _send_json(self, {"success": True, "notes": [_task_to_dict(t) for t in tasks]})
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # POST /api/notes  (action: add | update | delete | complete)
            if self.command == "POST" and parsed_url.path == "/api/notes":
                try:
                    raw = _read_body(self)
                    data = json.loads(raw.decode("utf-8")) if raw else {}
                    action = data.get("action", "add")

                    if action == "add":
                        new_id = TaskRepository.add(
                            task_type=data.get("task_type", "other"),
                            description=data.get("description", ""),
                            customer_name=data.get("customer_name", ""),
                            amount=float(data.get("amount", 0)),
                            notes=data.get("notes", ""),
                        )
                        TaskRepository.log_event(new_id, "created", "Created via Android")
                        _send_json(self, {"success": True, "id": new_id})

                    elif action == "update":
                        tid = int(data["id"])
                        TaskRepository.update(
                            task_id=tid,
                            task_type=data.get("task_type", "other"),
                            description=data.get("description", ""),
                            customer_name=data.get("customer_name", ""),
                            amount=float(data.get("amount", 0)),
                            notes=data.get("notes", ""),
                        )
                        _send_json(self, {"success": True})

                    elif action == "delete":
                        TaskRepository.delete(int(data["id"]))
                        _send_json(self, {"success": True})

                    elif action == "complete":
                        TaskRepository.mark_completed(int(data["id"]))
                        _send_json(self, {"success": True})

                    else:
                        _send_json(self, {"success": False, "error": "Unknown action"}, 400)

                    # Ping desktop UI to refresh task view
                    if (hasattr(self.server, "message_handler") and self.server.message_handler
                            and action in ("add", "update", "complete")):
                        try:
                            self.server.message_handler(
                                json.dumps({"command": "NOTES_UPDATED"})
                            )
                        except Exception:
                            pass
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # POST /api/qr-invoice
            if self.command == "POST" and parsed_url.path == "/api/qr-invoice":
                try:
                    raw = _read_body(self)
                    data = json.loads(raw.decode("utf-8"))
                    note_id = int(data["note_id"])
                    final_amount = float(data.get("final_amount", 0))
                    items = data.get("items", [])

                    bank = _load_bank_settings()
                    bin_code = bank.get("bin", "")
                    account = bank.get("account", "")
                    holder = bank.get("holder", "")

                    task = TaskRepository.get_by_id(note_id)
                    parts = [f"GC{note_id}"]
                    if task and task.customer_name:
                        cust_short = task.customer_name.strip().split()[0]
                        if cust_short:
                            parts.append(cust_short)
                    if final_amount > 0:
                        amount_k = int(final_amount // 1000)
                        if amount_k > 0:
                            parts.append(f"{amount_k}K")
                    transfer_content = " ".join(parts)
                    if len(transfer_content) > 50:
                        transfer_content = transfer_content[:47] + "..."

                    vietqr_url = ""
                    if bin_code and account:
                        from urllib.parse import quote
                        vietqr_url = (
                            f"https://img.vietqr.io/image/{bin_code}-{account}-compact.png"
                            f"?amount={int(final_amount)}&addInfo={quote(transfer_content)}"
                            f"&accountName={quote(holder)}"
                        )

                    if items:
                        TaskRepository.save_invoice_items(note_id, items)

                    TaskRepository.update_payment(note_id, "pending", vietqr_url, transfer_content)
                    TaskRepository.log_event(note_id, "qr_created", f"VietQR link generated, amount={int(final_amount)}")

                    _send_json(self, {
                        "success": True,
                        "note_id": note_id,
                        "transfer_content": transfer_content,
                        "vietqr_url": vietqr_url,
                    })

                    if hasattr(self.server, "message_handler") and self.server.message_handler:
                        try:
                            self.server.message_handler(json.dumps({"command": "NOTES_UPDATED"}))
                        except Exception:
                            pass
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # POST /api/notes/match  (Android calls after each bank notification)
            if self.command == "POST" and parsed_url.path == "/api/notes/match":
                try:
                    raw = _read_body(self)
                    data = json.loads(raw.decode("utf-8")) if raw else {}
                    content = data.get("content", "")
                    pkg = data.get("package", "")

                    from ..services.bank_parser import BankStatementParser
                    parsed = BankStatementParser.parse(content)
                    amount_str = parsed.get("amount", "") or ""
                    transfer_content = parsed.get("transfer_content", "") or ""

                    matched_task = None
                    matched_by = ""

                    # Auto-match only when note code is present (GC/INV formats).
                    note_code = BankStatementParser.extract_note_code(content + " " + transfer_content)
                    if note_code:
                        matched_task = TaskRepository.find_pending_by_code(note_code)
                        if matched_task:
                            matched_by = "code"

                    if matched_task:
                        TaskRepository.complete_payment(matched_task.id, source=f"Android/{pkg}")
                        TaskRepository.log_event(
                            matched_task.id, "payment_matched",
                            f"Matched by {matched_by}: {amount_str}", pkg
                        )
                        # Notify desktop UI
                        if hasattr(self.server, "message_handler") and self.server.message_handler:
                            try:
                                self.server.message_handler(json.dumps({
                                    "command": "TASK_MATCHED",
                                    "note_id": matched_task.id,
                                    "note_code": matched_task.note_code,
                                    "amount": amount_str,
                                }))
                            except Exception:
                                pass
                        _send_json(self, {
                            "matched": True,
                            "note_id": matched_task.id,
                            "note_code": matched_task.note_code,
                            "amount": amount_str,
                        })
                    else:
                        TaskRepository.log_event(
                            0,
                            "payment_manual_review_needed",
                            "No GC/INV code found or no pending note matched",
                            json.dumps(
                                {
                                    "package": pkg,
                                    "amount": amount_str,
                                    "transfer_content": transfer_content,
                                    "content": (content or "")[:200],
                                },
                                ensure_ascii=False,
                            ),
                        )
                        _send_json(self, {"matched": False, "reason": "manual_review_required"})
                except Exception as e:
                    self.send_error(500, str(e))
                return

            # Routes with dynamic {id} — GET /api/notes/{id}/invoice or POST /api/notes/{id}/complete
            note_id_match = _re.match(r"^/api/notes/(\d+)/(invoice|complete)$", parsed_url.path)
            if note_id_match:
                note_id = int(note_id_match.group(1))
                sub = note_id_match.group(2)

                if self.command == "GET" and sub == "invoice":
                    try:
                        task = TaskRepository.get_by_id(note_id)
                        if not task:
                            _send_json(self, {"success": False, "error": "Not found"}, 404)
                            return
                        items = TaskRepository.get_invoice_items(note_id)
                        _send_json(self, {
                            "success": True,
                            "note": _task_to_dict(task),
                            "items": [
                                {"id": it.id, "product_name": it.product_name, "unit": it.unit,
                                 "qty": it.qty, "unit_price": it.unit_price, "line_total": it.line_total}
                                for it in items
                            ],
                        })
                    except Exception as e:
                        self.send_error(500, str(e))
                    return

                if self.command == "POST" and sub == "complete":
                    try:
                        TaskRepository.complete_payment(note_id, source="Android/manual")
                        TaskRepository.log_event(note_id, "payment_completed", "Completed via Android")
                        _send_json(self, {"success": True})
                        if hasattr(self.server, "message_handler") and self.server.message_handler:
                            try:
                                self.server.message_handler(json.dumps({"command": "NOTES_UPDATED"}))
                            except Exception:
                                pass
                    except Exception as e:
                        self.send_error(500, str(e))
                    return

            # --- NOTIFICATION API (Legacy) ---
            msg = None

            # Log incoming request
            if hasattr(self.server, "logger"):
                self.server.logger.debug(
                    f"Received {self.command} request from {client_ip} to {self.path}"
                )

            # 1. Try to get content from URL query (?content=...)
            query_params = parse_qs(parsed_url.query)

            if "content" in query_params:
                msg = query_params["content"][0]

            # 2. If not in URL, try to get from request body
            if not msg:
                # If body was already read during auth key extraction, reuse it
                _peeked = getattr(self, "_peeked_body", None)

                content_length = self.headers.get("Content-Length")
                transfer_encoding = self.headers.get("Transfer-Encoding", "").lower()

                post_data = None
                if _peeked is not None:
                    # Body was already consumed during auth — reuse it
                    post_data = _peeked.decode("utf-8", errors="replace")
                elif content_length and int(content_length) > 0:
                    # Validate content length (prevent DoS)
                    if int(content_length) > 10240:  # 10KB max
                        self.send_error(413, "Payload Too Large")
                        return
                    post_data = self.rfile.read(int(content_length)).decode("utf-8", errors="replace")
                elif "chunked" in transfer_encoding:
                    # Chunked transfer — used by Cloudflare / reverse proxies
                    chunks: list = []
                    total = 0
                    try:
                        while True:
                            size_line = self.rfile.readline().decode("utf-8", errors="replace").strip()
                            if not size_line:
                                break
                            chunk_size = int(size_line.split(";")[0], 16)
                            if chunk_size == 0:
                                break
                            if total + chunk_size > 10240:  # 10KB DoS guard
                                self.send_error(413, "Payload Too Large")
                                return
                            chunk = self.rfile.read(chunk_size)
                            chunks.append(chunk)
                            total += chunk_size
                            self.rfile.read(2)  # consume CRLF
                    except Exception:
                        pass
                    if chunks:
                        post_data = b"".join(chunks).decode("utf-8", errors="replace")

                if post_data is not None:

                    # Validate Content-Type if present
                    content_type = self.headers.get("Content-Type", "")

                    if "application/json" in content_type:
                        try:
                            data = json.loads(post_data)

                            # Check if it's structured notification
                            if isinstance(data, dict):
                                # If it's a test ping from Android app
                                if data.get("content") == "Ping":
                                    # Auth passed (we got here), server is up,
                                    # message_handler is the bridge to desktop UI
                                    has_handler = bool(
                                        hasattr(self.server, "message_handler")
                                        and self.server.message_handler
                                    )
                                    pong = {
                                        "status": "success",
                                        "message": "pong",
                                        "auth": "ok",
                                        "handler": has_handler,
                                        "ready": has_handler,
                                    }
                                    if not has_handler:
                                        pong["error"] = "Desktop UI handler not registered — notifications will be lost"

                                    self.send_response(200)
                                    self.send_header("Content-Type", "application/json")
                                    self.end_headers()
                                    self.wfile.write(
                                        json.dumps(pong).encode("utf-8")
                                    )

                                    # ALSO notify Desktop UI
                                    if has_handler:
                                        self.server.message_handler(post_data)
                                    return

                                if "content" in data:
                                    msg = json.dumps(data, ensure_ascii=False)
                                else:
                                    msg = post_data
                            else:
                                msg = post_data
                        except json.JSONDecodeError:
                            self.send_error(400, "Invalid JSON")
                            return
                    else:
                        # Plain text content
                        msg = post_data

            # Validate message content (Accept everything if msg exists)
            if msg:
                # Sanitize message
                msg = self._sanitize_message(msg)

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
                    # Safe logging
                    try:
                        safe_msg = msg[:50].encode("ascii", "replace").decode("ascii")
                        self.server.logger.info(f"Notification received: {safe_msg}...")
                    except:
                        pass
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

    def _touch_heartbeat(self):
        """Notify heartbeat that this client IP is active."""
        try:
            heartbeat = getattr(self.server, "heartbeat", None)
            if heartbeat:
                heartbeat.touch_device(self.client_address[0])
        except Exception:
            pass

    def do_POST(self):
        """Handle POST requests"""
        self._touch_heartbeat()
        self.handle_request()

    def do_GET(self):
        """Handle GET requests"""
        self._touch_heartbeat()
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
        container=None,
    ):
        """
        Initialize notification service.

        Args:
            host: Server host address
            port: Server port
            logger: Logger instance
            max_requests_per_minute: Rate limit threshold
            container: Dependency injection container
        """
        self.host = host
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.container = container
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
            self.server.container = self.container  # Pass container to handler
            self.server.heartbeat = getattr(self, "heartbeat", None)

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
