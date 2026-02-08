"""
Alert Service - Inventory alerts and notifications
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional

from core.interfaces import IProductRepository, ISessionRepository


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    title: str
    message: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertService:
    """
    Service for inventory alerts and notifications.
    
    Features:
    - Low stock alerts
    - Out of stock alerts
    - High usage alerts
    - Custom threshold alerts
    """
    
    def __init__(
        self,
        product_repo: IProductRepository,
        session_repo: ISessionRepository,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize alert service.
        
        Args:
            product_repo: Product repository
            session_repo: Session repository
            logger: Logger instance
        """
        self.product_repo = product_repo
        self.session_repo = session_repo
        self.logger = logger or logging.getLogger(__name__)
        
        # Alert thresholds
        self.low_stock_threshold = 10  # units
        self.critical_stock_threshold = 5  # units
        self.high_usage_threshold = 0.8  # 80% of handover
        
        # Alert handlers
        self._handlers: List[Callable[[Alert], None]] = []
        
        self.logger.info("AlertService initialized")
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """
        Register alert handler callback.
        
        Args:
            handler: Function to call when alert is triggered
        """
        self._handlers.append(handler)
        self.logger.debug(f"Registered alert handler: {handler.__name__}")
    
    def check_all_alerts(self) -> List[Alert]:
        """
        Check all alert conditions.
        
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        try:
            # Get current session data
            sessions = self.session_repo.get_all()
            
            for session in sessions:
                # Check low stock
                if 0 < session.closing_qty <= self.critical_stock_threshold:
                    alert = Alert(
                        id=f"critical_stock_{session.product.id}",
                        level=AlertLevel.CRITICAL,
                        title="Hết hàng!",
                        message=f"{session.product.name}: Chỉ còn {session.closing_qty} {session.product.large_unit}",
                        product_id=session.product.id,
                        product_name=session.product.name
                    )
                    alerts.append(alert)
                    self._trigger_alert(alert)
                
                elif 0 < session.closing_qty <= self.low_stock_threshold:
                    alert = Alert(
                        id=f"low_stock_{session.product.id}",
                        level=AlertLevel.WARNING,
                        title="Sắp hết hàng",
                        message=f"{session.product.name}: Còn {session.closing_qty} {session.product.large_unit}",
                        product_id=session.product.id,
                        product_name=session.product.name
                    )
                    alerts.append(alert)
                    self._trigger_alert(alert)
                
                # Check out of stock
                if session.closing_qty == 0 and session.handover_qty > 0:
                    alert = Alert(
                        id=f"out_of_stock_{session.product.id}",
                        level=AlertLevel.CRITICAL,
                        title="Đã hết hàng!",
                        message=f"{session.product.name}: Đã hết hàng hoàn toàn",
                        product_id=session.product.id,
                        product_name=session.product.name
                    )
                    alerts.append(alert)
                    self._trigger_alert(alert)
                
                # Check high usage
                if session.handover_qty > 0:
                    usage_rate = session.used_qty / session.handover_qty
                    if usage_rate >= self.high_usage_threshold:
                        alert = Alert(
                            id=f"high_usage_{session.product.id}",
                            level=AlertLevel.WARNING,
                            title="Tiêu thụ cao",
                            message=f"{session.product.name}: Đã dùng {usage_rate*100:.0f}% ({session.used_qty}/{session.handover_qty})",
                            product_id=session.product.id,
                            product_name=session.product.name
                        )
                        alerts.append(alert)
                        self._trigger_alert(alert)
            
            if alerts:
                self.logger.info(f"Found {len(alerts)} alerts")
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
            return []
    
    def check_low_stock(self) -> List[Alert]:
        """
        Check for low stock alerts only.
        
        Returns:
            List of low stock alerts
        """
        alerts = []
        
        try:
            sessions = self.session_repo.get_all()
            
            for session in sessions:
                if 0 < session.closing_qty <= self.low_stock_threshold:
                    alert = Alert(
                        id=f"low_stock_{session.product.id}",
                        level=AlertLevel.WARNING,
                        title="Sắp hết hàng",
                        message=f"{session.product.name}: Còn {session.closing_qty} {session.product.large_unit}",
                        product_id=session.product.id,
                        product_name=session.product.name
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking low stock: {e}")
            return []
    
    def check_out_of_stock(self) -> List[Alert]:
        """
        Check for out of stock alerts only.
        
        Returns:
            List of out of stock alerts
        """
        alerts = []
        
        try:
            sessions = self.session_repo.get_all()
            
            for session in sessions:
                if session.closing_qty == 0 and session.handover_qty > 0:
                    alert = Alert(
                        id=f"out_of_stock_{session.product.id}",
                        level=AlertLevel.CRITICAL,
                        title="Đã hết hàng!",
                        message=f"{session.product.name}: Đã hết hàng hoàn toàn",
                        product_id=session.product.id,
                        product_name=session.product.name
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking out of stock: {e}")
            return []
    
    def _trigger_alert(self, alert: Alert):
        """
        Trigger alert by calling all registered handlers.
        
        Args:
            alert: Alert to trigger
        """
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")
    
    def set_low_stock_threshold(self, threshold: int):
        """Set low stock threshold."""
        self.low_stock_threshold = threshold
        self.logger.info(f"Low stock threshold set to: {threshold}")
    
    def set_critical_stock_threshold(self, threshold: int):
        """Set critical stock threshold."""
        self.critical_stock_threshold = threshold
        self.logger.info(f"Critical stock threshold set to: {threshold}")
    
    def set_high_usage_threshold(self, threshold: float):
        """Set high usage threshold (0.0 - 1.0)."""
        self.high_usage_threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"High usage threshold set to: {threshold*100:.0f}%")
