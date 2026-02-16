from services.bank_parser import BankStatementParser
from services.tts_service import TTSService
import os

# Test amount extraction for 1 million
msgs = [
    "Biến động số dư: GD +1,000,000VND",
    "Biến động số dư: GD -1,000,000VND",
    "GD 1.000.000 tu NGUYEN VAN A",
    "Thanh toan 1,000,000 cho dich vu"
]

for msg in msgs:
    res = BankStatementParser.parse(msg)
    print(f"Msg: {msg}")
    print(f"Extracted Amount: {res['amount']}")
    
    # Simulate TTS message generation logic
    amount = res['amount']
    is_outgoing = amount.strip().startswith('-')
    action_text = "Đã chuyển" if is_outgoing else "Đã nhận"
    amount_clean = "".join(filter(str.isdigit, amount))
    if amount_clean:
        amount_int = int(amount_clean)
        print(f"TTS will say: {action_text} {amount_int} đồng")
    print("-" * 20)
