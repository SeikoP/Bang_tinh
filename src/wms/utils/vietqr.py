"""
VietQR EMVCo Payload Generator

Generates QR code payloads following the EMV QR Code Specification for Payment Systems
(EMV QRCPS) used by NAPAS / VietQR.

Reference: https://www.emvco.com/specifications/emv-qr-code-specification-for-payment-systems/
"""

from __future__ import annotations


def _tlv(tag: str, value: str) -> str:
    """Build a TLV (Tag-Length-Value) field per EMVCo spec."""
    return f"{tag}{len(value):02d}{value}"


def _crc16_ccitt(data: str) -> str:
    """CRC-16/CCITT-FALSE used by EMVCo QR (poly=0x1021, init=0xFFFF)."""
    crc = 0xFFFF
    for byte in data.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_emvco_payload(
    bank_bin: str,
    account_number: str,
    amount: int | None = None,
    add_info: str = "",
) -> str:
    """
    Build a VietQR EMVCo merchant-presented QR payload string.

    Parameters
    ----------
    bank_bin : str
        NAPAS BIN code (e.g. "970415" for Vietinbank).
    account_number : str
        Beneficiary bank account number.
    amount : int | None
        Transaction amount in VND.  ``None`` or ``0`` → open amount.
    add_info : str
        Free-text transfer memo (max ~50 chars).

    Returns
    -------
    str
        The full EMVCo payload string ready to encode as a QR code.
    """
    # 00 - Payload Format Indicator
    parts = [_tlv("00", "01")]

    # 01 - Point of Initiation Method: 12 = dynamic (amount/info may change)
    parts.append(_tlv("01", "12"))

    # 38 - Merchant Account Information (NAPAS / VietQR)
    #   00: AID for NAPAS
    #   01: Bank BIN
    #   02: Account number
    ma_inner = (
        _tlv("00", "A000000727")
        + _tlv("01", bank_bin)
        + _tlv("02", account_number)
    )
    parts.append(_tlv("38", ma_inner))

    # 52 - Merchant Category Code
    parts.append(_tlv("52", "5999"))

    # 53 - Transaction Currency (704 = VND)
    parts.append(_tlv("53", "704"))

    # 54 - Transaction Amount (optional)
    if amount and amount > 0:
        parts.append(_tlv("54", str(int(amount))))

    # 58 - Country Code
    parts.append(_tlv("58", "VN"))

    # 62 - Additional Data
    if add_info:
        ad_inner = _tlv("08", add_info[:50])
        parts.append(_tlv("62", ad_inner))

    # 63 - CRC (placeholder → compute)
    payload_without_crc = "".join(parts) + "6304"
    crc = _crc16_ccitt(payload_without_crc)
    return payload_without_crc + crc


def generate_qr_pixmap(
    payload: str,
    scale: int = 10,
    border: int = 2,
):
    """
    Generate a ``QPixmap`` from an EMVCo payload string using segno.

    Parameters
    ----------
    payload : str
        EMVCo payload (from :func:`build_emvco_payload`).
    scale : int
        Pixels per QR module.
    border : int
        Quiet-zone modules around the QR code.

    Returns
    -------
    QPixmap
        The rendered QR image ready for display in a QLabel.
    """
    from io import BytesIO

    import segno
    from PyQt6.QtGui import QPixmap

    qr = segno.make_qr(payload, error="m", boost_error=False)
    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, border=border, dark="#000000", light="#ffffff")
    buf.seek(0)

    pixmap = QPixmap()
    pixmap.loadFromData(buf.read())
    return pixmap


def generate_qr_data_url(payload: str, scale: int = 6, border: int = 4) -> str:
    """
    Return a ``data:image/png;base64,…`` URL containing the QR image.

    The recipient pastes this text into any browser address bar →
    a perfect QR image is displayed and can be scanned from screen.

    Parameters
    ----------
    payload : str
        EMVCo (or any) payload to encode.
    scale : int
        Pixels per QR module (6 ≈ 200 px wide, good for scanning).
    border : int
        Quiet-zone modules (QR spec recommends 4).

    Returns
    -------
    str
        A ``data:`` URL string, typically 800–1200 characters.
    """
    import base64
    from io import BytesIO

    import segno

    qr = segno.make_qr(payload, error="l", boost_error=False)
    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, border=border, dark="#000000", light="#ffffff")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_qr_text(
    payload: str,
    dark: str = "X",
    light: str = " ",
    border: int = 1,
    mode: str = "ascii",
) -> str:
    """
    Render a QR payload as text using segno.

    Modes:
    - ``ascii``: one module per character (dark/light)
    - ``braille``: packs 2x4 modules per char using Braille Unicode blocks;
      this avoids regular spaces and is usually more stable in text-only channels.
        - ``halfblock``: packs 1x2 modules using Unicode half blocks (▀/▄/█),
            often closer to square modules on chat fonts.
        - ``block``: one module per character using ``█`` / ``░`` (no spaces),
            useful when target app trims or normalizes whitespace.
        - ``double``: two characters per module (``██``/``░░``),
            compensates for the ~1:2 width:height ratio of monospace fonts.
        - ``doublehalf``: **recommended** — double-width halfblock:
            merges 2 QR rows per text line (``▀▀``/``▄▄``/``██``/``░░``).
            Halves line count → reduces line-spacing distortion.
            Best scan reliability for text-only channels.
    """
    import io

    import segno

    qr = segno.make_qr(payload, error="l", boost_error=False)
    if mode == "doublehalf":
        matrix = [list(map(bool, row)) for row in qr.matrix]
        if not matrix:
            return ""
        src_h = len(matrix)
        src_w = len(matrix[0])
        w = src_w + 2 * border
        h = src_h + 2 * border
        canvas = [[False] * w for _ in range(h)]
        for y in range(src_h):
            for x in range(src_w):
                canvas[y + border][x + border] = matrix[y][x]
        if len(canvas) % 2:
            canvas.append([False] * w)
        lines: list[str] = []
        for y in range(0, len(canvas), 2):
            chars: list[str] = []
            top = canvas[y]
            bot = canvas[y + 1]
            for x in range(len(top)):
                t, b = top[x], bot[x]
                if t and b:
                    chars.append("██")
                elif t:
                    chars.append("▀▀")
                elif b:
                    chars.append("▄▄")
                else:
                    chars.append("░░")
            lines.append("".join(chars))
        return "\n".join(lines)

    if mode == "double":
        buf = io.StringIO()
        qr.save(buf, kind="txt", dark="1", light="0", border=border)
        raw = buf.getvalue().rstrip("\n")
        lines: list[str] = []
        for row in raw.split("\n"):
            lines.append(row.replace("1", "██").replace("0", "░░"))
        return "\n".join(lines)

    if mode == "braille":
        matrix = [list(map(bool, row)) for row in qr.matrix]
        if not matrix:
            return ""

        src_h = len(matrix)
        src_w = len(matrix[0])
        w = src_w + 2 * border
        h = src_h + 2 * border

        # Canvas with explicit quiet-zone so text render is scanner-friendly.
        canvas = [[False for _ in range(w)] for _ in range(h)]
        for y in range(src_h):
            row = matrix[y]
            for x in range(src_w):
                canvas[y + border][x + border] = row[x]

        # Braille cells encode 2x4 pixels. Pad to whole cells.
        pad_w = (2 - (w % 2)) % 2
        pad_h = (4 - (h % 4)) % 4
        if pad_w or pad_h:
            for row in canvas:
                row.extend([False] * pad_w)
            for _ in range(pad_h):
                canvas.append([False] * (w + pad_w))

        # Bit mapping for braille codepoints (U+2800 base).
        dot_map = (
            (0, 0, 0x01),  # dot 1
            (0, 1, 0x02),  # dot 2
            (0, 2, 0x04),  # dot 3
            (1, 0, 0x08),  # dot 4
            (1, 1, 0x10),  # dot 5
            (1, 2, 0x20),  # dot 6
            (0, 3, 0x40),  # dot 7
            (1, 3, 0x80),  # dot 8
        )

        lines: list[str] = []
        for y in range(0, len(canvas), 4):
            chars: list[str] = []
            for x in range(0, len(canvas[0]), 2):
                bits = 0
                for dx, dy, bit in dot_map:
                    if canvas[y + dy][x + dx]:
                        bits |= bit
                chars.append(chr(0x2800 + bits))
            lines.append("".join(chars))

        return "\n".join(lines)

    if mode == "halfblock":
        matrix = [list(map(bool, row)) for row in qr.matrix]
        if not matrix:
            return ""

        src_h = len(matrix)
        src_w = len(matrix[0])
        w = src_w + 2 * border
        h = src_h + 2 * border

        canvas = [[False for _ in range(w)] for _ in range(h)]
        for y in range(src_h):
            row = matrix[y]
            for x in range(src_w):
                canvas[y + border][x + border] = row[x]

        # Need even height because each output row encodes two QR rows.
        if len(canvas) % 2:
            canvas.append([False] * len(canvas[0]))

        lines: list[str] = []
        for y in range(0, len(canvas), 2):
            chars: list[str] = []
            top = canvas[y]
            bottom = canvas[y + 1]
            for x in range(len(top)):
                t = top[x]
                b = bottom[x]
                if t and b:
                    chars.append("█")
                elif t:
                    chars.append("▀")
                elif b:
                    chars.append("▄")
                else:
                    chars.append(" ")
            lines.append("".join(chars).rstrip())

        return "\n".join(lines).rstrip("\n")

    if mode == "block":
        buf = io.StringIO()
        qr.save(buf, kind="txt", dark="█", light="░", border=border)
        return buf.getvalue().rstrip("\n")

    buf = io.StringIO()
    qr.save(buf, kind="txt", dark=dark, light=light, border=border)
    return buf.getvalue().rstrip("\n")
