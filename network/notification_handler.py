"""
Notification Handler - HTTP request handler for Android notifications
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse


class NotificationHandler(BaseHTTPRequestHandler):
    """Server xử lý thông báo từ app Android - Filter tại PC"""

    # Danh sách package name của các app ngân hàng Việt Nam + test packages
    BANK_PACKAGES = {
        "com.vnpay.wallet",  # VNPay
        "com.vietcombank.mobile",  # Vietcombank
        "com.techcombank.bb.app",  # Techcombank
        "com.mbmobile",  # MB Bank
        "com.vnpay.bidv",  # BIDV
        "com.acb.acbmobile",  # ACB
        "com.tpb.mb.gprsandroid",  # TPBank
        "com.msb.mbanking",  # MSB
        "com.vietinbank.ipay",  # VietinBank
        "com.agribank.mobilebanking",  # Agribank
        "com.sacombank.mbanking",  # Sacombank
        "com.hdbank.mobilebanking",  # HDBank
        "com.vpbank.mobilebanking",  # VPBank
        "com.ocb.mobilebanking",  # OCB
        "com.shb.mobilebanking",  # SHB
        "com.scb.mobilebanking",  # SCB
        "com.seabank.mobilebanking",  # SeaBank
        "com.vib.mobilebanking",  # VIB
        "com.lienvietpostbank.mobilebanking",  # LienVietPostBank
        "com.bvbank.mobilebanking",  # BaoVietBank
        "com.pvcombank.mobilebanking",  # PVcomBank
        "com.mservice.momotransfer",  # MoMo
        # Test packages ONLY for adb testing - remove in production
        "android",  # For adb test notifications
        "com.android.shell",  # For adb test notifications
    }

    def handle_request(self):
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
                    self.wfile.write(b'{"status":"error","message":"Unauthorized: Missing or invalid token"}')
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.warning(f"Unauthorized request from {self.client_address}")
                    return
                
                token = auth_header.split(" ")[1].strip()
                if token != expected_key:
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status":"error","message":"Forbidden: Invalid token"}')
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.warning(f"Forbidden request from {self.client_address}: Invalid token")
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

                        # Try to parse content if it's a JSON string
                        try:
                            content_data = json.loads(raw_content)
                            if isinstance(content_data, dict):
                                # Extract actual content from nested structure
                                content = content_data.get("content", raw_content)
                            else:
                                content = raw_content
                        except (json.JSONDecodeError, TypeError):
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

    def do_POST(self):
        self.handle_request()

    def do_GET(self):
        self.handle_request()

    def log_message(self, format, *args):
        # Silent logging - use server logger instead
        return
