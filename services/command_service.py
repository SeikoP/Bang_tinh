"""
Command Service - Undo/Redo functionality using Command Pattern
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional


class Command(ABC):
    """
    Abstract base class for commands.

    Implements Command Pattern for undo/redo functionality.
    """

    @abstractmethod
    def execute(self):
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self):
        """Undo the command."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get command description for UI."""
        pass


class UpdateQuantityCommand(Command):
    """Command for updating product quantity."""

    def __init__(
        self,
        session_repo,
        product_id: int,
        product_name: str,
        old_handover: int,
        old_closing: int,
        new_handover: int,
        new_closing: int,
    ):
        self.session_repo = session_repo
        self.product_id = product_id
        self.product_name = product_name
        self.old_handover = old_handover
        self.old_closing = old_closing
        self.new_handover = new_handover
        self.new_closing = new_closing

    def execute(self):
        """Execute: Update to new quantities."""
        self.session_repo.update_qty(
            self.product_id, self.new_handover, self.new_closing
        )

    def undo(self):
        """Undo: Restore old quantities."""
        self.session_repo.update_qty(
            self.product_id, self.old_handover, self.old_closing
        )

    def get_description(self) -> str:
        return f"Cập nhật số lượng: {self.product_name}"


class AddProductCommand(Command):
    """Command for adding a product."""

    def __init__(
        self,
        product_repo,
        session_repo,
        name: str,
        large_unit: str,
        conversion: int,
        unit_price: float,
    ):
        self.product_repo = product_repo
        self.session_repo = session_repo
        self.name = name
        self.large_unit = large_unit
        self.conversion = conversion
        self.unit_price = unit_price
        self.product_id: Optional[int] = None

    def execute(self):
        """Execute: Add product."""
        self.product_id = self.product_repo.add(
            self.name, self.large_unit, self.conversion, self.unit_price
        )

    def undo(self):
        """Undo: Delete product (soft delete)."""
        if self.product_id:
            self.product_repo.delete(self.product_id, soft_delete=True)

    def get_description(self) -> str:
        return f"Thêm sản phẩm: {self.name}"


class DeleteProductCommand(Command):
    """Command for deleting a product."""

    def __init__(self, product_repo, product_id: int, product_name: str):
        self.product_repo = product_repo
        self.product_id = product_id
        self.product_name = product_name
        self.product_data = None

    def execute(self):
        """Execute: Delete product (soft delete)."""
        # Save product data for undo
        self.product_data = self.product_repo.get_by_id(self.product_id)
        self.product_repo.delete(self.product_id, soft_delete=True)

    def undo(self):
        """Undo: Restore product (set is_active=1)."""
        if self.product_data:
            # Restore by updating is_active flag
            # This requires adding a restore method to repository
            # For now, we'll update the product
            self.product_repo.update(
                self.product_id,
                self.product_data.name,
                self.product_data.large_unit,
                self.product_data.conversion,
                float(self.product_data.unit_price),
            )

    def get_description(self) -> str:
        return f"Xóa sản phẩm: {self.product_name}"


class UpdateProductCommand(Command):
    """Command for updating a product."""

    def __init__(
        self,
        product_repo,
        product_id: int,
        old_name: str,
        old_large_unit: str,
        old_conversion: int,
        old_unit_price: float,
        new_name: str,
        new_large_unit: str,
        new_conversion: int,
        new_unit_price: float,
    ):
        self.product_repo = product_repo
        self.product_id = product_id
        self.old_name = old_name
        self.old_large_unit = old_large_unit
        self.old_conversion = old_conversion
        self.old_unit_price = old_unit_price
        self.new_name = new_name
        self.new_large_unit = new_large_unit
        self.new_conversion = new_conversion
        self.new_unit_price = new_unit_price

    def execute(self):
        """Execute: Update to new values."""
        self.product_repo.update(
            self.product_id,
            self.new_name,
            self.new_large_unit,
            self.new_conversion,
            self.new_unit_price,
        )

    def undo(self):
        """Undo: Restore old values."""
        self.product_repo.update(
            self.product_id,
            self.old_name,
            self.old_large_unit,
            self.old_conversion,
            self.old_unit_price,
        )

    def get_description(self) -> str:
        return f"Sửa sản phẩm: {self.new_name}"


class CommandHistory:
    """
    Manages command history for undo/redo functionality.

    Features:
    - Execute commands
    - Undo last command
    - Redo undone command
    - Clear history
    - Get history for UI
    """

    def __init__(self, max_history: int = 50, logger: Optional[logging.Logger] = None):
        """
        Initialize command history.

        Args:
            max_history: Maximum number of commands to keep in history
            logger: Logger instance
        """
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self.max_history = max_history
        self.logger = logger or logging.getLogger(__name__)

        self.logger.info("CommandHistory initialized")

    def execute(self, command: Command):
        """
        Execute a command and add to history.

        Args:
            command: Command to execute
        """
        try:
            # Execute command
            command.execute()

            # Add to undo stack
            self._undo_stack.append(command)

            # Clear redo stack (can't redo after new command)
            self._redo_stack.clear()

            # Limit history size
            if len(self._undo_stack) > self.max_history:
                self._undo_stack.pop(0)

            self.logger.debug(f"Executed: {command.get_description()}")

        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise

    def undo(self) -> bool:
        """
        Undo last command.

        Returns:
            True if undo successful, False if nothing to undo
        """
        if not self.can_undo():
            return False

        try:
            # Pop from undo stack
            command = self._undo_stack.pop()

            # Undo command
            command.undo()

            # Add to redo stack
            self._redo_stack.append(command)

            self.logger.info(f"Undone: {command.get_description()}")
            return True

        except Exception as e:
            self.logger.error(f"Undo failed: {e}")
            # Put command back on undo stack
            self._undo_stack.append(command)
            raise

    def redo(self) -> bool:
        """
        Redo last undone command.

        Returns:
            True if redo successful, False if nothing to redo
        """
        if not self.can_redo():
            return False

        try:
            # Pop from redo stack
            command = self._redo_stack.pop()

            # Execute command again
            command.execute()

            # Add back to undo stack
            self._undo_stack.append(command)

            self.logger.info(f"Redone: {command.get_description()}")
            return True

        except Exception as e:
            self.logger.error(f"Redo failed: {e}")
            # Put command back on redo stack
            self._redo_stack.append(command)
            raise

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def get_undo_description(self) -> Optional[str]:
        """Get description of command that will be undone."""
        if self.can_undo():
            return self._undo_stack[-1].get_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of command that will be redone."""
        if self.can_redo():
            return self._redo_stack[-1].get_description()
        return None

    def clear(self):
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.logger.info("Command history cleared")

    def get_history(self, limit: int = 10) -> List[str]:
        """
        Get recent command history for UI.

        Args:
            limit: Maximum number of commands to return

        Returns:
            List of command descriptions
        """
        return [cmd.get_description() for cmd in self._undo_stack[-limit:]]
