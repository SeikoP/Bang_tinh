import re

class MockParser:
    _AMOUNT_COMPILED = [
        re.compile(r'(?:Giao\s+dich|So\s+tien|GD|ST):\s*([\+\-]?[\d,\.]{3,15})\s*(?:VND|d|dong)?', re.IGNORECASE),
        re.compile(r'([\+\-]\d{1,3}(?:[,\.]\d{3})+)', re.IGNORECASE),
        re.compile(r'([\+\-]?\d{1,3}(?:[,\.]\d{3})+)\s*(?:VND|d|dong)', re.IGNORECASE),
        re.compile(r'([\+\-]\d{4,12})', re.IGNORECASE),
    ]

    @classmethod
    def extract_amount(cls, message):
        for compiled_re in cls._AMOUNT_COMPILED:
            match = compiled_re.search(message)
            if match:
                return match.group(1)
        return None

msgs = [
    "Biến động số dư: GD +1,000,000VND",
    "Biến động số dư: GD -1,000,000VND",
    "ST: - 1,000,000",
    "GD 1.000.000 tu NGUYEN VAN A", # This one should fail Regex 1-4 if no VND and no ST
    "GD: 1.000.000",
]

for msg in msgs:
    amt = MockParser.extract_amount(msg)
    print(f"Msg: {msg} -> Extracted: {amt}")
