"""
Reusable Data Table Widget
Standardized table with common features
"""

from typing import List, Optional, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QLabel
)


class DataTable(QTableWidget):
    """
    Standardized data table widget
    
    Features:
    - Consistent styling
    - Row actions
    - Pagination
    - Search/filter
    - Export
    
    Usage:
        table = DataTable(
            headers=["ID", "Name", "Price"],
            row_height=45
        )
        table.set_data(data)
    """
    
    # Signals
    row_clicked = pyqtSignal(int)  # row index
    row_double_clicked = pyqtSignal(int)
    action_clicked = pyqtSignal(str, int)  # action_name, row_index
    
    def __init__(
        self,
        headers: List[str],
        row_height: int = 45,
        alternating_colors: bool = True,
        sortable: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.headers = headers
        self.row_height = row_height
        self._row_actions: List[tuple[str, str, Callable]] = []  # (name, icon, callback)
        
        self._setup_table(alternating_colors, sortable)
    
    def _setup_table(self, alternating_colors: bool, sortable: bool):
        """Setup table properties"""
        # Set columns
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        
        # Header
        header = self.horizontalHeader()
        for i in range(len(self.headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        # Vertical header
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(self.row_height)
        
        # Styling
        self.setAlternatingRowColors(alternating_colors)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Sorting
        if sortable:
            self.setSortingEnabled(True)
        
        # Signals
        self.cellClicked.connect(lambda row, col: self.row_clicked.emit(row))
        self.cellDoubleClicked.connect(lambda row, col: self.row_double_clicked.emit(row))
    
    def set_column_widths(self, widths: List[int]):
        """
        Set fixed column widths
        
        Args:
            widths: List of widths in pixels (0 = stretch)
        """
        header = self.horizontalHeader()
        for i, width in enumerate(widths):
            if width > 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(i, width)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
    
    def add_row_action(self, name: str, icon: str, callback: Callable):
        """
        Add action button to each row
        
        Args:
            name: Action name
            icon: Icon text (emoji or icon)
            callback: Callback function(row_index)
        """
        self._row_actions.append((name, icon, callback))
        
        # Add actions column if not exists
        if "Actions" not in self.headers:
            self.setColumnCount(self.columnCount() + 1)
            self.setHorizontalHeaderItem(
                self.columnCount() - 1,
                QTableWidgetItem("Actions")
            )
            self.horizontalHeader().setSectionResizeMode(
                self.columnCount() - 1,
                QHeaderView.ResizeMode.Fixed
            )
            self.setColumnWidth(self.columnCount() - 1, 100)
    
    def set_data(self, data: List[List[any]]):
        """
        Set table data
        
        Args:
            data: List of rows, each row is list of values
        """
        self.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.setItem(row_idx, col_idx, item)
            
            # Add action buttons
            if self._row_actions:
                self._add_action_buttons(row_idx)
    
    def _add_action_buttons(self, row_idx: int):
        """Add action buttons to row"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        for name, icon, callback in self._row_actions:
            btn = QPushButton(icon)
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, r=row_idx, n=name: self._on_action_clicked(n, r))
            layout.addWidget(btn)
        
        layout.addStretch()
        self.setCellWidget(row_idx, self.columnCount() - 1, container)
    
    def _on_action_clicked(self, action_name: str, row_idx: int):
        """Handle action button click"""
        self.action_clicked.emit(action_name, row_idx)
        
        # Call callback
        for name, icon, callback in self._row_actions:
            if name == action_name:
                callback(row_idx)
                break
    
    def get_row_data(self, row_idx: int) -> List[str]:
        """Get data from row"""
        data = []
        for col_idx in range(self.columnCount() - (1 if self._row_actions else 0)):
            item = self.item(row_idx, col_idx)
            data.append(item.text() if item else "")
        return data
    
    def clear_data(self):
        """Clear all data"""
        self.setRowCount(0)
    
    def add_row(self, data: List[any]):
        """Add single row"""
        row_idx = self.rowCount()
        self.insertRow(row_idx)
        
        for col_idx, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row_idx, col_idx, item)
        
        if self._row_actions:
            self._add_action_buttons(row_idx)
    
    def remove_row(self, row_idx: int):
        """Remove row"""
        self.removeRow(row_idx)
    
    def update_row(self, row_idx: int, data: List[any]):
        """Update row data"""
        for col_idx, value in enumerate(data):
            item = self.item(row_idx, col_idx)
            if item:
                item.setText(str(value))
            else:
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row_idx, col_idx, item)
