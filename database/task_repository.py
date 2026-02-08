"""
Task repository for work notes
"""

from datetime import datetime
from typing import List, Optional

from database.connection import get_connection
from database.task_models import Task


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
    def add(task_type: str, description: str, customer_name: str = "", 
            amount: float = 0, notes: str = "") -> int:
        """Add new task"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_type, description, customer_name, amount, 
                                 created_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task_type, description, customer_name, amount, 
                  datetime.now().isoformat(), notes))
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
                query = "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                tasks.append(Task(
                    id=row[0],
                    task_type=row[1],
                    description=row[2],
                    customer_name=row[3] or "",
                    amount=row[4] or 0,
                    created_at=datetime.fromisoformat(row[5]),
                    completed=bool(row[6]),
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    notes=row[8] or ""
                ))
            
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
            
            tasks = []
            for row in rows:
                tasks.append(Task(
                    id=row[0],
                    task_type=row[1],
                    description=row[2],
                    customer_name=row[3] or "",
                    amount=row[4] or 0,
                    created_at=datetime.fromisoformat(row[5]),
                    completed=bool(row[6]),
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    notes=row[8] or ""
                ))
            
            return tasks
    
    @staticmethod
    def get_by_id(task_id: int) -> Optional[Task]:
        """Get task by ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return Task(
                    id=row[0],
                    task_type=row[1],
                    description=row[2],
                    customer_name=row[3] or "",
                    amount=row[4] or 0,
                    created_at=datetime.fromisoformat(row[5]),
                    completed=bool(row[6]),
                    completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    notes=row[8] or ""
                )
            return None
    
    @staticmethod
    def update(task_id: int, task_type: str, description: str, 
               customer_name: str = "", amount: float = 0, notes: str = ""):
        """Update task"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks 
                SET task_type = ?, description = ?, customer_name = ?, 
                    amount = ?, notes = ?
                WHERE id = ?
            """, (task_type, description, customer_name, amount, notes, task_id))
            conn.commit()
    
    @staticmethod
    def mark_completed(task_id: int):
        """Mark task as completed"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks 
                SET completed = 1, completed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), task_id))
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
                (task_type,)
            )
            return cursor.fetchone()[0]
