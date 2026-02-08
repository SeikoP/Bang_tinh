"""
Bank Statement Parser - Advanced parsing for Vietnamese bank notifications
"""

import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any


class BankStatementParser:
    """
    Intelligent parser for Vietnamese bank transaction messages
    
    Handles multiple formats from different banks:
    - VietinBank, Vietcombank, MB Bank, etc.
    - Extracts sender name, amount, datetime, content
    """
    
    # Noise patterns to remove (Only for content cleaning, AFTER extraction attempt)
    NOISE_PATTERNS = [
        r'CT\s+DEN:\w+', 
        r'CT\s+DI:\w+',  
        r'MBVCB\.\d+(\.\d+)*', 
        r'FT\d+',        
        r'Ref:\w+',      
        r'GD:\d+',       
        r'Ma\s+GD:\s*\w+',
        r'Nap\s+tu\s+the\s+le', # MoMo noise
    ]
    
    # Sender name patterns (ordered by priority)
    SENDER_PATTERNS = [
        # Format: "CT DEN:xxx NGUYEN VAN A chuyen tien" (Search before cleaning noise)
        r'CT\s+DEN:\w+\s+([A-Z][A-Z\s]{2,50}?)\s+(?:chuyen|nhan|gui)',
        
        # Format: "CT tu 9386565885 DINH CONG LUONG toi ..."
        r'tu\s+\d+\s+([A-Z][A-Z\s]{2,50}?)(\s+toi|$)',
        
        # Format: "tu [NAME] - ND: ..."
        r'tu\s+([A-Z][A-Z\s]{2,50}?)(?:\s+-\s+ND:|\s+chuyen|\s+nhan)',
        
        # Format: "NGUYEN VAN A chuyen tien"
        r'([A-Z][A-Z\s]{2,40}?)\s+(?:chuyen\s+tien|nhan\s+tien|gui\s+tien|chuyen\s+khoan)',
        
        # Format: "Noi dung: NGUYEN VAN A chuyen tien"
        r'Noi\s+dung:\s*([A-Z][A-Z\s]{2,40}?)\s+(?:chuyen|nhan|gui)',
        
        # Format: "ND: NGUYEN VAN A [CODES]"
        r'ND:\s*([A-Z][A-Z\s]{2,40}?)(?:\s+chuyen|\s+nhan|\s*FT|\s*MBVCB|\s*;|\.|\s*$)',
        
        # Format: "Nhan tien tu NGUYEN VAN A"
        r'(?:Nhan|Chuyen)\s+tien\s+tu\s+([A-Z][A-Z\s]{2,40}?)',

        # Format: Just uppercase name before transaction codes
        r'([A-Z][A-Z\s]{2,40}?)\s+(?:FT\d+|MBVCB|Ref:)',
    ]
    
    # Amount patterns
    AMOUNT_PATTERNS = [
        r'Giao\s+dich:\s*([\+\-]?[\d,\.]+)\s*(?:VND|d|dong)?',
        r'So\s+tien:\s*([\+\-]?[\d,\.]+)\s*(?:VND|d|dong)?',
        r'([\+\-]\d{1,3}(?:[,\.]\d{3})+)', # +100.000 or -100,000
        r'([\+\-]?\d{1,3}(?:[,\.]\d{3})+)\s*(?:VND|d|dong)',
    ]
    
    # Datetime patterns
    DATETIME_PATTERNS = [
        (r'Thoi\s+gian:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', '%d/%m/%Y %H:%M'),
        (r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})', '%d/%m/%Y %H:%M:%S'),
        (r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2})', '%d-%m-%Y %H:%M'),
        (r'(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2})', '%d/%m/%y %H:%M'),
    ]
    
    @classmethod
    def parse(cls, raw_message: str) -> Dict[str, Any]:
        """
        Parse bank notification message
        """
        # 1. Normalize accents for internal matching
        normalized = cls._strip_accents(raw_message).replace('\\n', ' ').replace('\\', '')
        
        # 2. Extract components BEFORE heavy noise cleaning
        sender_name = cls._extract_sender_name(normalized)
        amount = cls._extract_amount(normalized)
        dt = cls._extract_datetime(normalized)
        source = cls.detect_source(raw_message)
        
        # 3. Clean message for UI display
        cleaned = cls._clean_message(normalized)
        
        return {
            'sender_name': sender_name,
            'amount': amount,
            'datetime': dt,
            'source': source,
            'content': cleaned,
            'raw_content': raw_message
        }
    
    @classmethod
    def _clean_message(cls, normalized_msg: str) -> str:
        """Remove noise patterns and normalize text for display"""
        cleaned = normalized_msg
        
        # Remove noise patterns
        for pattern in cls.NOISE_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    @staticmethod
    def _strip_accents(s: str) -> str:
        """Normalize Vietnamese characters to ASCII"""
        nfkd_form = unicodedata.normalize('NFKD', s)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    @classmethod
    def _extract_sender_name(cls, message: str) -> Optional[str]:
        """
        Extract sender name from message
        """
        for pattern in cls.SENDER_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                
                # Check for "noise words" that might be captured
                noise_words = ['SOI', 'TIEN', 'GIAO', 'DICH', 'THOI', 'GIAN', 'VIETINBANK', 'VCB', 'MBBANK']
                if any(w == name for w in noise_words):
                    continue

                # Clean up name
                name = cls._clean_sender_name(name)
                
                # Validate name (at least 2 words, > 5 chars)
                if len(name) >= 5 and (len(name.split()) >= 2 or name.isupper()):
                    return name
        
        return None
    
    @classmethod
    def _clean_sender_name(cls, name: str) -> str:
        """Clean and validate sender name"""
        # Remove trailing noises caught in capture group
        name = re.sub(r'\s+(chuyen|nhan|gui|tien|khoan|tu|den|so|tien|gd|ma|ref).*$', '', name, flags=re.IGNORECASE)
        
        # Remove transaction codes
        name = re.sub(r'\s+(FT\d+|MBVCB|Ref:).*$', '', name, flags=re.IGNORECASE)
        
        # Final cleanup
        name = re.sub(r'[^a-zA-Z\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Title case (Nguyen Van A)
        if name:
            words = name.split()
            return ' '.join(w.capitalize() for w in words)
        return ""
    
    @classmethod
    def _extract_amount(cls, message: str) -> Optional[str]:
        """
        Extract transaction amount
        
        Returns:
            Amount string with +/- prefix or None
        """
        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount = match.group(1)
                
                # Ensure +/- prefix
                if not amount.startswith(('+', '-')):
                    # Detect transaction type from keywords
                    if cls._is_incoming_transaction(message):
                        amount = '+' + amount
                    else:
                        amount = '-' + amount
                
                return amount
        
        return None
    
    @classmethod
    def _is_incoming_transaction(cls, message: str) -> bool:
        """Detect if transaction is incoming (receiving money)"""
        incoming_keywords = [
            'nhan tien', 'cong tien', 'tien vao', 'nap tien',
            'hoan tien', 'received', 'credit'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in incoming_keywords)
    
    @classmethod
    def _extract_datetime(cls, message: str) -> Optional[datetime]:
        """
        Extract transaction datetime
        
        Returns:
            datetime object or None
        """
        for pattern, date_format in cls.DATETIME_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    dt_str = match.group(1)
                    return datetime.strptime(dt_str, date_format)
                except ValueError:
                    continue
        
    @classmethod
    def detect_source(cls, message: str) -> str:
        """Detect bank/app source from message keywords"""
        msg_lower = message.lower()
        if 'vietinbank' in msg_lower: return 'VietinBank'
        if 'vcb' in msg_lower or 'vietcombank' in msg_lower: return 'Vietcombank'
        if 'mb bank' in msg_lower or 'mbb' in msg_lower: return 'MB Bank'
        if 'tpb' in msg_lower or 'tien phong' in msg_lower: return 'TPBank'
        if 'acb' in msg_lower: return 'ACB'
        if 'momo' in msg_lower: return 'Momo'
        if 'zalopay' in msg_lower: return 'ZaloPay'
        return 'Bank'


if __name__ == "__main__":
    # Test cases
    test_messages = [
        """Biến động số dư: Thời gian: 07/02/2026 03:30
Tài khoản: 107875070594
Giao dịch: +67,000VND
Số dư hiện tại: 1,545,606VND
Nội dung: CT DEN:422T2620B9D1SN8M MBVCB.12922428728.350539.DINH CONG LUONG chuyen tien.CT tu 9386565885 DINH CONG LUONG toi 107875070594 NGUYEN HUU CUONG tai VIETINBANK""",
        
        """Biến động số dư: Thời gian: 07/02/2026 03:13
Tài khoản: 107875070594
Giao dịch: +20,000VND
Số dư hiện tại: 1,478,606VND
Nội dung: CT DEN:422T2620B8Q43T2H PHAN NGUYEN NAM ANH chuyen tien""",
        
        """Biến động số dư: Thời gian: 07/02/2026 02:51
Tài khoản: 107875070594
Giao dịch: +20,000VND
Số dư hiện tại: 1,458,606VND
Nội dung: CT DEN:603719547897 NGUYEN XUAN TRUNG chuyen tien FT26038869732008; tai Napas"""
    ]
    
    for msg in test_messages:
        result = BankStatementParser.parse(msg)
        print(f"\nSource: {result['source']}")
        print(f"Sender: {result['sender_name']}")
        print(f"Amount: {result['amount']}")
        print(f"DateTime: {result['datetime']}")
