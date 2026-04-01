"""
Task repository for work notes
"""

import re
from datetime import datetime
from typing import List, Optional

from .connection import get_connection
from .task_models import Task, InvoiceItem, NoteEvent


def _row_to_task(row) -> Task:
    """Convert a DB row to a Task object (handles old 9-col and new 12-col rows)."""
    return Task(
        id=row[0],
        task_type=row[1],
        description=row[2],
        customer_name=row[3] or "",
        amount=row[4] or 0,
        created_at=datetime.fromisoformat(row[5]),
        completed=bool(row[6]),
        completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
        notes=row[8] or "",
        payment_status=row[9] if len(row) > 9 and row[9] else "none",
        transfer_content=row[10] if len(row) > 10 and row[10] else "",
        vietqr_url=row[11] if len(row) > 11 and row[11] else "",
    )


class TaskRepository:
    """Repository for task operations"""

    @staticmethod
    def create_table():
        """Create tasks table if not exists"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    customer_name TEXT,
                    amount REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    completed_at TEXT,
                    notes TEXT
                )
            """)
            conn.commit()

    @staticmethod
    def add(
        task_type: str,
        description: str,
        customer_name: str = "",
        amount: float = 0,
        notes: str = "",
    ) -> int:
        """Add new task"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (task_type, description, customer_name, amount, 
                                 created_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    task_type,
                    description,
                    customer_name,
                    amount,
                    datetime.now().isoformat(),
                    notes,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all(include_completed: bool = False) -> List[Task]:
        """Get all tasks"""
        with get_connection() as conn:
            cursor = conn.cursor()

            if include_completed:
                query = "SELECT * FROM tasks ORDER BY completed ASC, created_at DESC"
            else:
                query = (
                    "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at DESC"
                )

            cursor.execute(query)
            rows = cursor.fetchall()

            tasks = [_row_to_task(row) for row in rows]
            return tasks

    @staticmethod
    def get_by_type(task_type: str, include_completed: bool = False) -> List[Task]:
        """Get tasks by type"""
        with get_connection() as conn:
            cursor = conn.cursor()

            if include_completed:
                query = "SELECT * FROM tasks WHERE task_type = ? ORDER BY completed ASC, created_at DESC"
                cursor.execute(query, (task_type,))
            else:
                query = "SELECT * FROM tasks WHERE task_type = ? AND completed = 0 ORDER BY created_at DESC"
                cursor.execute(query, (task_type,))

            rows = cursor.fetchall()
            tasks = [_row_to_task(row) for row in rows]
            return tasks

    @staticmethod
    def get_by_id(task_id: int) -> Optional[Task]:
        """Get task by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                return _row_to_task(row)
            return None

    @staticmethod
    def update(
        task_id: int,
        task_type: str,
        description: str,
        customer_name: str = "",
        amount: float = 0,
        notes: str = "",
    ):
        """Update task"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET task_type = ?, description = ?, customer_name = ?, 
                    amount = ?, notes = ?
                WHERE id = ?
            """,
                (task_type, description, customer_name, amount, notes, task_id),
            )
            conn.commit()

    @staticmethod
    def mark_completed(task_id: int):
        """Mark task as completed"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks 
                SET completed = 1, completed_at = ?
                WHERE id = ?
            """,
                (datetime.now().isoformat(), task_id),
            )
            conn.commit()

    @staticmethod
    def delete(task_id: int):
        """Delete task"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    @staticmethod
    def count_pending() -> int:
        """Count pending tasks"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0")
            return cursor.fetchone()[0]

    @staticmethod
    def count_pending_by_type(task_type: str) -> int:
        """Count pending tasks by type"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE task_type = ? AND completed = 0",
                (task_type,),
            )
            return cursor.fetchone()[0]

    # ─────────────────────────────────────────
    # Payment / VietQR helpers
    # ─────────────────────────────────────────

    @staticmethod
    def update_payment(
        task_id: int,
        payment_status: str,
        vietqr_url: str = "",
        transfer_content: str = "",
    ) -> None:
        """Update payment_status, VietQR URL and transfer content on a task."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tasks
                SET payment_status = ?, vietqr_url = ?, transfer_content = ?
                WHERE id = ?
                """,
                (payment_status, vietqr_url, transfer_content, task_id),
            )
            conn.commit()

    @staticmethod
    def complete_payment(task_id: int, source: str = "") -> bool:
        """
        Idempotently complete a task as paid.
        Does nothing (returns True) if already completed.
        Returns True on success, False if task not found.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT completed, payment_status FROM tasks WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            if row[0] or row[1] == "completed":
                return True  # already done — idempotent
            cursor.execute(
                """
                UPDATE tasks
                SET completed = 1, completed_at = ?, payment_status = 'completed'
                WHERE id = ?
                """,
                (datetime.now().isoformat(), task_id),
            )
            conn.commit()
        TaskRepository.log_event(task_id, "payment_completed", f"Auto-matched by {source or 'system'}")
        return True

    @staticmethod
    def find_pending_by_code(note_code: str) -> Optional[Task]:
        """
        Find first unpaid+pending task by note code.
        Supports GC{ID} and INV-YYYY-MM-ID formats.
        """
        if not note_code:
            return None
        match = re.search(
            r"\b(?:GC(?P<gc>\d+)|INV(?:-\d{4}-\d{2})?-(?P<inv>\d+))\b",
            str(note_code),
            re.IGNORECASE,
        )
        if not match:
            return None
        raw_id = match.group("gc") or match.group("inv")
        try:
            note_id = int(raw_id)
        except (TypeError, ValueError):
            return None
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE id = ? AND completed = 0 AND task_type = 'unpaid'
                  AND payment_status IN ('pending', 'none')
                """,
                (note_id,),
            )
            row = cursor.fetchone()
            return _row_to_task(row) if row else None

    @staticmethod
    def find_pending_by_amount(
        amount: float, tolerance: float = 1000
    ) -> Optional[Task]:
        """
        FIFO: find oldest unpaid+pending task whose amount is within tolerance.
        Returns the first (oldest) match, or None.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE completed = 0 AND task_type = 'unpaid'
                  AND payment_status IN ('pending', 'none')
                  AND amount BETWEEN ? AND ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (amount - tolerance, amount + tolerance),
            )
            row = cursor.fetchone()
            return _row_to_task(row) if row else None

    @staticmethod
    def find_pending_payments() -> List[Task]:
        """Return all unpaid tasks with payment_status='pending'."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE task_type = 'unpaid' AND payment_status = 'pending'
                  AND completed = 0
                ORDER BY created_at DESC
                """
            )
            return [_row_to_task(r) for r in cursor.fetchall()]

    # ─────────────────────────────────────────
    # Invoice items
    # ─────────────────────────────────────────

    @staticmethod
    def save_invoice_items(note_id: int, items: list) -> None:
        """
        Replace all invoice items for note_id.
        Each item dict: {product_id, product_name, unit, qty, unit_price, line_total, item_note}
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoice_items WHERE note_id = ?", (note_id,))
            for it in items:
                cursor.execute(
                    """
                    INSERT INTO invoice_items
                        (note_id, product_id, product_name, unit, qty, unit_price, line_total, item_note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note_id,
                        it.get("product_id", 0),
                        it.get("product_name", it.get("name", "")),
                        it.get("unit", ""),
                        it.get("qty", 1),
                        it.get("unit_price", 0),
                        it.get("line_total", it.get("qty", 1) * it.get("unit_price", 0)),
                        it.get("item_note", ""),
                    ),
                )
            conn.commit()

    @staticmethod
    def get_invoice_items(note_id: int) -> List[InvoiceItem]:
        """Return invoice items for a note."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM invoice_items WHERE note_id = ? ORDER BY id ASC",
                (note_id,),
            )
            result = []
            for r in cursor.fetchall():
                result.append(
                    InvoiceItem(
                        id=r[0],
                        note_id=r[1],
                        product_id=r[2] or 0,
                        product_name=r[3],
                        unit=r[4] or "",
                        qty=r[5] or 1,
                        unit_price=r[6] or 0,
                        line_total=r[7] or 0,
                        item_note=r[8] or "",
                    )
                )
            return result

    # ─────────────────────────────────────────
    # Event log
    # ─────────────────────────────────────────

    @staticmethod
    def log_event(
        note_id: int,
        event_type: str,
        message: str = "",
        metadata: str = "",
    ) -> None:
        """Append an event to the note event log."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO note_events (note_id, event_type, message, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (note_id, event_type, message, metadata, datetime.now().isoformat()),
            )
            conn.commit()

    @staticmethod
    def get_events(note_id: int) -> List[NoteEvent]:
        """Return all events for a note, newest first."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM note_events WHERE note_id = ? ORDER BY created_at DESC",
                (note_id,),
            )
            result = []
            for r in cursor.fetchall():
                result.append(
                    NoteEvent(
                        id=r[0],
                        note_id=r[1],
                        event_type=r[2],
                        message=r[3] or "",
                        metadata=r[4] or "",
                        created_at=datetime.fromisoformat(r[5]),
                    )
                )
            return result

    @staticmethod
    def get_manual_review_events(limit: int = 200) -> List[NoteEvent]:
        """Return manual-review payment events, newest first."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM note_events
                WHERE event_type = 'payment_manual_review_needed'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            result = []
            for r in cursor.fetchall():
                result.append(
                    NoteEvent(
                        id=r[0],
                        note_id=r[1],
                        event_type=r[2],
                        message=r[3] or "",
                        metadata=r[4] or "",
                        created_at=datetime.fromisoformat(r[5]),
                    )
                )
            return result

    @staticmethod
    def count_manual_review_events() -> int:
        """Count pending manual-review payment events."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM note_events
                WHERE event_type = 'payment_manual_review_needed'
                """
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    @staticmethod
    def delete_event(event_id: int) -> None:
        """Delete a note event by id."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM note_events WHERE id = ?", (event_id,))
            conn.commit()

