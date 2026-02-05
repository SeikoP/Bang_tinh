"""
Calculation View - Màn hình bảng tính dịch vụ
Thiết kế hiện đại và đồng nhất
"""
import flet as ft
from flet import Icons, Colors
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import AppTheme
from ui.components.dialogs import SaveSessionDialog
from database import SessionRepository, HistoryRepository
from services import CalculatorService, ReportService


class CalculationView(ft.Container):
    """View bảng tính dịch vụ - Premium Design"""
    
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker = None, on_navigate: callable = None, is_dark: bool = False):
        self._page = page
        self.on_navigate = on_navigate
        self.is_dark = is_dark
        self.calc_service = CalculatorService()
        self.report_service = ReportService()
        
        # Use provided FilePicker (already in overlay)
        self.html_picker = file_picker
        
        # Initialize UI
        self._build_ui()
        
        super().__init__(
            content=ft.Column([
                self._build_header(),
                ft.Container(height=16),
                self.report_container, # Thêm phần hiển thị báo cáo
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column([self.calc_table], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    **AppTheme.card_style(self.is_dark),
                ),
                ft.Container(height=12),
                self._build_footer(),
            ]),
            padding=0,
            expand=True,
        )
        
        # Load data
        self.refresh_table(update=False)
    
    def _build_ui(self):
        """Build UI components"""
        self.total_text = ft.Text(
            "Tổng cộng: 0 VNĐ",
            size=22,
            weight=ft.FontWeight.W_700,
            color=AppTheme.PRIMARY,
        )
        
        self.calc_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Đ.Vị", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Tên sản phẩm", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Giao ca", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Chốt ca", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Quy đổi", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Đã dùng", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Đơn giá", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Thành tiền", weight=ft.FontWeight.W_600, size=13)),
            ],
            rows=[],
            **AppTheme.data_table_style(self.is_dark),
        )

        # Container cho báo cáo HTML
        self.report_container = ft.Container(visible=False)
    
    def _build_header(self) -> ft.Container:
        """Build header section - Premium style"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(Icons.CALCULATE_ROUNDED, color=Colors.WHITE, size=22),
                        width=42,
                        height=42,
                        bgcolor=AppTheme.PRIMARY,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(
                            "Kê khai Dịch vụ",
                            size=22,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            "Tính toán chi phí sử dụng sản phẩm",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=14),
                ft.Row([
                    ft.Button(
                        "Nhập báo cáo HTML",
                        icon=Icons.UPLOAD_FILE_ROUNDED,
                        on_click=lambda _: self._handle_file_pick(),
                        style=AppTheme.secondary_button_style(self.is_dark),
                    ),
                    ft.Button(
                        "Làm mới",
                        icon=Icons.REFRESH_ROUNDED,
                        on_click=lambda e: self.refresh_table(),
                        style=AppTheme.secondary_button_style(self.is_dark),
                    ),
                    ft.Button(
                        "Lưu phiên",
                        icon=Icons.SAVE_ROUNDED,
                        on_click=lambda e: self._show_save_dialog(),
                        style=AppTheme.primary_button_style(),
                    ),
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 16, 0, 0),
        )
    
    def _build_footer(self) -> ft.Container:
        """Build footer section - Clean summary"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.INFO_OUTLINE_ROUNDED, color=AppTheme.INFO, size=16),
                        ft.Text(
                            "Nhập định dạng: 3t4 = 3 thùng 4 đơn vị",
                            size=12,
                            color=AppTheme.INFO,
                        ),
                    ], spacing=6),
                    bgcolor=Colors.with_opacity(0.1, AppTheme.INFO),
                    padding=ft.Padding(12, 8, 12, 8),
                    border_radius=AppTheme.RADIUS_MD,
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.MONETIZATION_ON_ROUNDED, color=AppTheme.SUCCESS, size=22),
                        self.total_text,
                    ], spacing=8),
                    bgcolor=Colors.with_opacity(0.1, AppTheme.SUCCESS),
                    padding=ft.Padding(20, 12, 20, 12),
                    border_radius=AppTheme.RADIUS_LG,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(16, 8, 16, 16),
        )

    def _build_report_section(self, data: Dict[str, Any]):
        """Hiển thị kết quả parse file HTML"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.ANALYTICS_ROUNDED, color=AppTheme.PRIMARY),
                    ft.Text(f"Báo cáo: {data['file_name']}", weight=ft.FontWeight.BOLD, size=14),
                    ft.IconButton(Icons.CLOSE_ROUNDED, icon_size=16, on_click=lambda _: self._hide_report()),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1, color=AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT),
                ft.Row([
                    self._report_item("Tiền thực tế", f"{data['actual_total']:,.0f} đ", Icons.MONEY_ROUNDED, AppTheme.PRIMARY),
                    self._report_item("Tiền thực thu", f"{data['received_total']:,.0f} đ", Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, AppTheme.SUCCESS),
                    self._report_item("Lượt 50,000", f"{data['count_50k']} lượt", Icons.COUNTERTOPS_ROUNDED, AppTheme.WARNING),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=20),
            ], spacing=10),
            **AppTheme.card_style(self.is_dark),
            padding=16,
        )

    def _report_item(self, label, value, icon, color):
        return ft.Column([
            ft.Row([ft.Icon(icon, color=color, size=18), ft.Text(label, size=12, color=AppTheme.TEXT_SECONDARY_LIGHT)], spacing=4),
            ft.Text(value, size=16, weight=ft.FontWeight.W_700, color=color),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def on_file_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if not e.files or len(e.files) == 0:
            return
        
        file_path = e.files[0].path
        result = self.report_service.parse_html_report(file_path)
        
        if result["success"]:
            self.report_container.content = self._build_report_section(result)
            self.report_container.visible = True
            self.update()
        else:
            self._page.snack_bar = ft.SnackBar(content=ft.Text(f"Lỗi: {result['error']}"))
            self._page.snack_bar.open = True
            self._page.update()
    
    def _handle_file_pick(self):
        """Trigger file picker dialog"""
        if self.html_picker:
            self.html_picker.pick_files(allowed_extensions=["html"], allow_multiple=False)

    def _hide_report(self):
        self.report_container.visible = False
        self.update()
    
    def refresh_table(self, update: bool = True):
        """Refresh dữ liệu bảng tính"""
        sessions = SessionRepository.get_all()
        self.calc_table.rows.clear()
        
        total_all = 0
        
        for s in sessions:
            product = s.product
            
            # Format display
            handover_disp = self.calc_service.format_to_display(
                s.handover_qty, product.conversion, product.unit_char
            )
            closing_disp = self.calc_service.format_to_display(
                s.closing_qty, product.conversion, product.unit_char
            )
            
            total_all += s.amount
            
            # Create input widgets
            handover_input = self._create_qty_input(
                product.id, s.handover_qty, handover_disp, product.conversion, True
            )
            closing_input = self._create_qty_input(
                product.id, s.closing_qty, closing_disp, product.conversion, False
            )
            
            # Thêm row
            used_color = AppTheme.SECONDARY if s.used_qty > 0 else Colors.with_opacity(0.3, AppTheme.TEXT_SECONDARY_LIGHT)
            
            self.calc_table.rows.append(
                ft.DataRow(cells=[
                    # Đơn vị - Badge
                    ft.DataCell(ft.Container(
                        content=ft.Text(product.large_unit, size=11, color=Colors.WHITE, weight=ft.FontWeight.W_500),
                        bgcolor=AppTheme.PRIMARY,
                        padding=ft.Padding(8, 4, 8, 4),
                        border_radius=AppTheme.RADIUS_SM,
                    )),
                    # Tên SP
                    ft.DataCell(ft.Text(
                        product.name,
                        weight=ft.FontWeight.W_600,
                        size=14,
                        color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                    )),
                    # Giao ca
                    ft.DataCell(handover_input),
                    # Chốt ca
                    ft.DataCell(closing_input),
                    # Quy đổi
                    ft.DataCell(ft.Text(
                        f"{product.conversion}/{product.large_unit.lower()[0]}",
                        size=12,
                        color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                    )),
                    # Đã dùng - Badge
                    ft.DataCell(ft.Container(
                        content=ft.Text(
                            str(s.used_qty),
                            weight=ft.FontWeight.W_600,
                            size=13,
                            color=Colors.WHITE,
                        ),
                        bgcolor=used_color,
                        padding=ft.Padding(12, 6, 12, 6),
                        border_radius=AppTheme.RADIUS_SM,
                    )),
                    # Đơn giá
                    ft.DataCell(ft.Text(
                        f"{product.unit_price:,.0f}",
                        size=13,
                        color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                    )),
                    # Thành tiền - Highlighted
                    ft.DataCell(ft.Text(
                        f"{s.amount:,.0f}",
                        weight=ft.FontWeight.W_700,
                        size=14,
                        color=AppTheme.SUCCESS if s.amount > 0 else AppTheme.TEXT_SECONDARY_LIGHT,
                    )),
                ])
            )
        
        self.total_text.value = f"Tổng cộng: {total_all:,.0f} VNĐ"
        if update:
            self._page.update()
    
    def _create_qty_input(self, product_id: int, qty: int, display: str, 
                          conversion: int, is_handover: bool) -> ft.TextField:
        """Tạo input widget cho số lượng"""
        
        def on_change(e):
            val_str = e.control.value
            new_qty = self.calc_service.parse_to_small_units(val_str, conversion)
            
            # Lấy dữ liệu hiện tại
            sessions = SessionRepository.get_all()
            current = next((s for s in sessions if s.product.id == product_id), None)
            if not current:
                return
            
            h_qty = new_qty if is_handover else current.handover_qty
            c_qty = current.closing_qty if is_handover else new_qty
            
            # MẶC ĐỊNH: Nếu thay đổi Giao ca, Chốt ca tự động bằng Giao ca (nếu không có thay đổi từ kho)
            if is_handover:
                c_qty = h_qty
            
            # Đảm bảo chốt ca không lớn hơn giao ca
            if c_qty > h_qty:
                c_qty = h_qty
            
            # Validate
            if not is_handover:
                is_valid, error = self.calc_service.validate_closing_qty(h_qty, c_qty)
                if not is_valid:
                    e.control.error_text = error
                    e.control.update()
                    return
                else:
                    e.control.error_text = None
            
            # Update DB
            SessionRepository.update_qty(product_id, h_qty, c_qty)
            self.refresh_table()
        
        input_field = ft.TextField(
            value=display if qty > 0 else "0",
            width=85,
            height=38,
            dense=True,
            text_size=13,
            text_align=ft.TextAlign.CENTER,
            border_radius=AppTheme.RADIUS_SM,
            border_color=AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT,
            focused_border_color=AppTheme.PRIMARY,
            on_submit=on_change,
            on_blur=on_change,
        )
        
        return input_field
    
    def _show_save_dialog(self):
        """Hiển thị dialog lưu phiên"""
        total = SessionRepository.get_total_amount()
        
        def on_save(data):
            HistoryRepository.save_current_session(
                shift_name=data['shift_name'],
                notes=data['notes']
            )
            SessionRepository.reset_all()
            dialog.open = False
            self._page.update()
            # Remove dialog from overlay to prevent accumulation
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)
            self.refresh_table()
            self._show_snackbar("Đã lưu phiên làm việc!", "success")
        
        def on_cancel():
            dialog.open = False
            self._page.update()
            # Remove dialog from overlay to prevent accumulation
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)
        
        dialog = SaveSessionDialog(
            total_amount=total,
            on_save=on_save,
            on_cancel=on_cancel,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _show_snackbar(self, message: str, type: str = "info"):
        """Hiển thị snackbar notification"""
        colors_map = {
            "success": AppTheme.SUCCESS,
            "warning": AppTheme.WARNING,
            "error": AppTheme.ERROR,
            "info": AppTheme.INFO,
        }
        self._page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(
                    Icons.CHECK_CIRCLE_ROUNDED if type == "success" else 
                    Icons.WARNING_ROUNDED if type == "warning" else
                    Icons.ERROR_ROUNDED if type == "error" else Icons.INFO_ROUNDED,
                    color=Colors.WHITE,
                    size=20,
                ),
                ft.Text(message, color=Colors.WHITE, weight=ft.FontWeight.W_500),
            ], spacing=10),
            bgcolor=colors_map.get(type, AppTheme.INFO),
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=20,
            padding=16,
        )
        self._page.snack_bar.open = True
        self._page.update()
