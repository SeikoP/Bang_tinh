"""
TaskViewModel — Backend for TaskView.qml
Manages tasks (unpaid, uncollected, undelivered items).
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import TaskListModel


class TaskViewModel(BaseViewModel):
    """ViewModel for task/note management."""

    taskAdded = Signal()
    taskUpdated = Signal()
    taskDeleted = Signal()
    dataRefreshed = Signal()
    filterChanged = Signal()
    pendingCountChanged = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._task_model = TaskListModel(self)
        self._filter_type = ""  # empty = all
        self._pending_count = 0

    @Property("QVariant", constant=True)
    def tasks(self):
        return self._task_model

    def _get_filter_type(self) -> str:
        return self._filter_type

    def _set_filter_type(self, val: str):
        if self._filter_type != val:
            self._filter_type = val
            self.filterChanged.emit()
            self.refreshData()

    filterType = Property(str, _get_filter_type, _set_filter_type, notify=filterChanged)

    def _get_pending_count(self) -> int:
        return self._pending_count

    pendingCount = Property(int, _get_pending_count, notify=pendingCountChanged)

    @Slot()
    def refreshData(self):
        """Reload tasks from database."""
        def _load():
            from database.task_repository import TaskRepository
            if self._filter_type:
                from database.task_models import TaskType
                try:
                    task_type = TaskType(self._filter_type)
                    tasks = TaskRepository.get_by_type(task_type.value)
                except ValueError:
                    tasks = TaskRepository.get_all()
            else:
                tasks = TaskRepository.get_all()
            self._task_model.resetItems(tasks)
            self._pending_count = TaskRepository.count_pending()
            self.pendingCountChanged.emit()
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh tasks")

    @Slot(str, str, str, float, str)
    def addTask(self, task_type: str, description: str, customer_name: str, amount: float, notes: str):
        """Add a new task."""
        def _add():
            from database.task_repository import TaskRepository
            from database.task_models import TaskType, Task
            try:
                tt = TaskType(task_type)
            except ValueError:
                tt = TaskType.OTHER
            task = Task(
                id=0,
                task_type=tt,
                description=description,
                customer_name=customer_name,
                amount=amount if amount > 0 else None,
                created_at=None,
                completed=False,
                completed_at=None,
                notes=notes or None,
            )
            TaskRepository.add(task)
            self.refreshData()
            self.taskAdded.emit()
        self._safe_call(_add, error_msg="Failed to add task")

    @Slot(int)
    def markCompleted(self, task_id: int):
        """Mark a task as completed."""
        def _complete():
            from database.task_repository import TaskRepository
            TaskRepository.mark_completed(task_id)
            self.refreshData()
            self.taskUpdated.emit()
        self._safe_call(_complete, error_msg="Failed to complete task")

    @Slot(int, str, str, str, float, str)
    def updateTask(self, task_id: int, task_type: str, description: str,
                   customer_name: str, amount: float, notes: str):
        """Update an existing task."""
        def _update():
            from database.task_repository import TaskRepository
            from database.task_models import TaskType
            try:
                tt = TaskType(task_type)
            except ValueError:
                tt = TaskType.OTHER
            TaskRepository.update(task_id, tt.value, description, customer_name,
                                  amount if amount > 0 else None, notes or None)
            self.refreshData()
            self.taskUpdated.emit()
        self._safe_call(_update, error_msg="Failed to update task")

    @Slot(int)
    def deleteTask(self, task_id: int):
        """Delete a task."""
        def _delete():
            from database.task_repository import TaskRepository
            TaskRepository.delete(task_id)
            self.refreshData()
            self.taskDeleted.emit()
        self._safe_call(_delete, error_msg="Failed to delete task")

    @Slot(result=list)
    def getTaskTypes(self) -> list:
        """Return available task type options for QML ComboBox."""
        from database.task_models import TaskType
        return [{"value": t.value, "label": t.value} for t in TaskType]
