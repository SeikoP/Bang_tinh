"""
ProductViewModel — Backend for ProductView.qml

Manages product CRUD and quick price entries.
"""

from decimal import Decimal

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import ProductListModel, QuickPriceModel


class ProductViewModel(BaseViewModel):
    """ViewModel for product management."""

    productAdded = Signal()
    productUpdated = Signal()
    productDeleted = Signal()
    dataRefreshed = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._product_model = ProductListModel(self)
        self._quick_price_model = QuickPriceModel(self)

    @Property("QVariant", constant=True)
    def products(self):
        return self._product_model

    @Property("QVariant", constant=True)
    def quickPrices(self):
        return self._quick_price_model

    @Slot()
    def refreshData(self):
        """Reload products and quick prices."""
        def _load():
            product_repo = self._get_service("product_repo")
            qp_repo = self._get_service("quick_price_repo")
            if product_repo:
                self._product_model.resetItems(product_repo.get_all())
            if qp_repo:
                self._quick_price_model.resetItems(qp_repo.get_all())
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh product data")

    @Slot(str, str, int, float)
    def addProduct(self, name: str, large_unit: str, conversion: int, unit_price: float):
        """Add a new product."""
        def _add():
            product_repo = self._get_service("product_repo")
            if not product_repo:
                return
            from core.models import Product
            product = Product(
                id=None,
                name=name,
                large_unit=large_unit,
                conversion=conversion,
                unit_price=Decimal(str(unit_price)),
            )
            product_repo.add(product)
            self.refreshData()
            self.productAdded.emit()
        self._safe_call(_add, error_msg="Failed to add product")

    @Slot(int, str, str, int, float)
    def updateProduct(self, product_id: int, name: str, large_unit: str, conversion: int, unit_price: float):
        """Update an existing product."""
        def _update():
            product_repo = self._get_service("product_repo")
            if not product_repo:
                return
            from core.models import Product
            product = Product(
                id=product_id,
                name=name,
                large_unit=large_unit,
                conversion=conversion,
                unit_price=Decimal(str(unit_price)),
            )
            product_repo.update(product)
            self.refreshData()
            self.productUpdated.emit()
        self._safe_call(_update, error_msg="Failed to update product")

    @Slot(int)
    def deleteProduct(self, product_id: int):
        """Soft-delete a product."""
        def _delete():
            product_repo = self._get_service("product_repo")
            if product_repo:
                product_repo.delete(product_id)
                self.refreshData()
                self.productDeleted.emit()
        self._safe_call(_delete, error_msg="Failed to delete product")

    @Slot(int)
    def toggleFavorite(self, product_id: int):
        """Toggle product favorite status."""
        def _toggle():
            product_repo = self._get_service("product_repo")
            if product_repo:
                product_repo.toggle_favorite(product_id)
                self.refreshData()
        self._safe_call(_toggle, error_msg="Failed to toggle favorite")

    # ---- Quick Price ----

    @Slot(str, float)
    def addQuickPrice(self, name: str, price: float):
        def _add():
            qp_repo = self._get_service("quick_price_repo")
            if qp_repo:
                from core.models import QuickPrice
                qp = QuickPrice(id=0, name=name, price=Decimal(str(price)))
                qp_repo.add(qp)
                self.refreshData()
        self._safe_call(_add, error_msg="Failed to add quick price")

    @Slot(int, str, float)
    def updateQuickPrice(self, qp_id: int, name: str, price: float):
        def _update():
            qp_repo = self._get_service("quick_price_repo")
            if qp_repo:
                from core.models import QuickPrice
                qp = QuickPrice(id=qp_id, name=name, price=Decimal(str(price)))
                qp_repo.update(qp)
                self.refreshData()
        self._safe_call(_update, error_msg="Failed to update quick price")

    @Slot(int)
    def deleteQuickPrice(self, qp_id: int):
        def _delete():
            qp_repo = self._get_service("quick_price_repo")
            if qp_repo:
                qp_repo.delete(qp_id)
                self.refreshData()
        self._safe_call(_delete, error_msg="Failed to delete quick price")
