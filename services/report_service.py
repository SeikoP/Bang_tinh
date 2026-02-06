import os
import re
from typing import Any, Dict

from bs4 import BeautifulSoup


class ReportService:
    """Service xử lý dữ liệu từ file HTML báo cáo"""

    @staticmethod
    def parse_html_report(file_path: str) -> Dict[str, Any]:
        """
        Parse nội dung file HTML và trích xuất các thông tin cần thiết.

        Args:
            file_path: Đường dẫn tới file HTML

        Returns:
            Dictionary chứa các thông tin: tổng tiền thực tế, thực thu, số lượt 50k
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "lxml")

            # 1. Lấy tổng tiền thực tế (thường nằm trong thẻ h3 hoặc bảng tổng)
            actual_total = 0
            # Tìm trong h3
            h3_texts = soup.find_all("h3")
            for h3 in h3_texts:
                if "Tổng tiền thực tế" in h3.text or "Tổng cộng" in h3.text:
                    actual_total = ReportService._clean_currency(h3.text)
                    if actual_total > 0:
                        break

            # 2. Lấy tổng tiền thực thu
            received_total = 0
            # Nếu không tìm thấy trong h3, duyệt qua các bảng
            tables = soup.find_all("table")

            count_50k = 0

            for table in tables:
                rows = table.find_all("tr")
                # Lấy header để xác định vị trí cột
                headers = (
                    [th.text.strip() for th in rows[0].find_all(["th", "td"])]
                    if rows
                    else []
                )

                # Tìm chỉ số cột "$ (Thực Thu)"
                col_idx = -1
                for i, h in enumerate(headers):
                    if "$ (Thực Thu)" in h or "Thực Thu" in h:
                        col_idx = i
                        break

                # Duyệt các dòng dữ liệu (bỏ qua dòng đầu là header)
                for row in rows[1:]:
                    cells = row.find_all("td")
                    if len(cells) <= col_idx or col_idx == -1:
                        continue

                    cell_text = cells[col_idx].text.strip()
                    if not cell_text or "Tổng cộng" in row.text:
                        continue

                    val = ReportService._clean_currency(cell_text)

                    # Đếm số lượt 50,000
                    if val == 50000:
                        count_50k += 1

                    # Nếu dòng này là dòng tổng cộng trong bảng (phòng trường hợp template khác)
                    if "tổng" in row.text.lower() and received_total == 0:
                        received_total = ReportService._clean_currency(cell_text)

            # Nếu vẫn chưa tìm thấy thực thu, lấy số liệu cuối cùng (thường là tổng)
            if received_total == 0:
                # Tìm thẻ nào có text "Thực thu"
                received_tags = soup.find_all(string=re.compile("Thực thu", re.I))
                for tag in received_tags:
                    parent = tag.parent
                    received_total = ReportService._clean_currency(parent.text)
                    if received_total > 0:
                        break

            return {
                "success": True,
                "actual_total": actual_total,
                "received_total": received_total,
                "count_50k": count_50k,
                "file_name": os.path.basename(file_path),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _clean_currency(text: str) -> int:
        """Chuẩn hóa chuỗi tiền tệ sang số nguyên"""
        if not text:
            return 0
        # Tìm các con số và dấu phân cách , .
        # Ví dụ: "Thực thu: 1,500,000 đ" -> "1500000"
        clean_str = re.sub(r"[^\d]", "", text)
        try:
            return int(clean_str) if clean_str else 0
        except ValueError:
            return 0
