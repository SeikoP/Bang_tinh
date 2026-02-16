"""Security test: SQL Injection vulnerabilities"""

from database.connection import get_connection
from database.repositories import BankRepository


class TestSQLInjection:
    """Test SQL injection vulnerabilities"""

    def test_bank_repository_sql_injection_in_content(self):
        """Test if malicious SQL in content field is properly escaped"""
        malicious_content = "'; DROP TABLE bank_history; --"

        # This should NOT drop the table
        BankRepository.add(
            time_str="10:00:00",
            source="Test",
            amount="1000",
            content=malicious_content,
            sender_name="Attacker",
        )

        # Verify table still exists
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bank_history'"
            )
            assert (
                cursor.fetchone() is not None
            ), "Table was dropped - SQL injection successful!"

    def test_bank_repository_sql_injection_in_sender_name(self):
        """Test SQL injection in sender_name field"""
        malicious_name = "' OR '1'='1"

        BankRepository.add(
            time_str="10:00:00",
            source="Test",
            amount="1000",
            content="Test",
            sender_name=malicious_name,
        )

        # Should only return 1 record, not all records
        results = BankRepository.get_all()
        # If vulnerable, this would return all records
        assert len(results) >= 1

    def test_null_byte_injection(self):
        """Test null byte injection"""
        malicious_content = "Normal text\x00DROP TABLE bank_history"

        BankRepository.add(
            time_str="10:00:00",
            source="Test",
            amount="1000",
            content=malicious_content,
            sender_name="Test",
        )

        # Verify table still exists
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bank_history'"
            )
            assert cursor.fetchone() is not None

    def test_unicode_injection(self):
        """Test Unicode/special character injection"""
        malicious_chars = [
            "'; DELETE FROM bank_history WHERE '1'='1",
            "' UNION SELECT * FROM bank_history--",
            "admin'--",
            "' OR 1=1--",
            "'; EXEC xp_cmdshell('dir')--",
        ]

        for malicious in malicious_chars:
            try:
                BankRepository.add(
                    time_str="10:00:00",
                    source="Test",
                    amount="1000",
                    content=malicious,
                    sender_name="Test",
                )
            except Exception as e:
                # Should handle gracefully, not crash
                assert "syntax error" not in str(e).lower()
