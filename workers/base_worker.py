"""
Base Worker Classes for Background Tasks
"""

import logging
import queue
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """Background task"""
    id: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
    
    def __lt__(self, other):
        """For priority queue sorting"""
        return self.priority.value > other.priority.value


class WorkerSignals(QObject):
    """Signals for worker communication"""
    started = pyqtSignal(str)  # task_id
    progress = pyqtSignal(str, int)  # task_id, progress (0-100)
    finished = pyqtSignal(str, object)  # task_id, result
    error = pyqtSignal(str, Exception)  # task_id, exception


class BaseWorker(QThread):
    """
    Base worker thread for background tasks
    
    Features:
    - Task queue with priority
    - Progress reporting
    - Error handling
    - Graceful shutdown
    """
    
    def __init__(self, name: str, logger: logging.Logger):
        super().__init__()
        self.name = name
        self.logger = logger
        self.signals = WorkerSignals()
        
        # Task queue (priority queue)
        self.task_queue = queue.PriorityQueue()
        
        # Control flags
        self._running = False
        self._paused = False
        
        # Statistics
        self.tasks_completed = 0
        self.tasks_failed = 0
    
    def add_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ):
        """
        Add task to queue
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            callback: Success callback (called on UI thread)
            error_callback: Error callback (called on UI thread)
        """
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            callback=callback,
            error_callback=error_callback
        )
        
        self.task_queue.put(task)
        self.logger.debug(f"[{self.name}] Task added: {task_id} (priority: {priority.name})")
    
    def run(self):
        """Worker main loop"""
        self._running = True
        self.logger.info(f"[{self.name}] Worker started")
        
        while self._running:
            try:
                # Get task with timeout (allows checking _running flag)
                try:
                    task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Check if paused
                while self._paused and self._running:
                    time.sleep(0.1)
                
                if not self._running:
                    break
                
                # Execute task
                self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"[{self.name}] Worker error: {e}", exc_info=True)
        
        self.logger.info(f"[{self.name}] Worker stopped")
    
    def _execute_task(self, task: Task):
        """Execute single task"""
        try:
            self.logger.debug(f"[{self.name}] Executing task: {task.id}")
            self.signals.started.emit(task.id)
            
            # Execute function
            result = task.func(*task.args, **task.kwargs)
            
            # Success
            self.tasks_completed += 1
            self.signals.finished.emit(task.id, result)
            
            # Call callback on UI thread
            if task.callback:
                task.callback(result)
            
            self.logger.debug(f"[{self.name}] Task completed: {task.id}")
            
        except Exception as e:
            # Error
            self.tasks_failed += 1
            self.logger.error(f"[{self.name}] Task failed: {task.id} - {e}", exc_info=True)
            self.signals.error.emit(task.id, e)
            
            # Call error callback on UI thread
            if task.error_callback:
                task.error_callback(e)
    
    def pause(self):
        """Pause worker"""
        self._paused = True
        self.logger.info(f"[{self.name}] Worker paused")
    
    def resume(self):
        """Resume worker"""
        self._paused = False
        self.logger.info(f"[{self.name}] Worker resumed")
    
    def stop(self):
        """Stop worker gracefully"""
        self._running = False
        self.logger.info(f"[{self.name}] Stopping worker...")
        self.wait(5000)  # Wait up to 5 seconds
    
    def get_stats(self) -> dict:
        """Get worker statistics"""
        return {
            'name': self.name,
            'running': self._running,
            'paused': self._paused,
            'queue_size': self.task_queue.qsize(),
            'completed': self.tasks_completed,
            'failed': self.tasks_failed
        }


class WorkerPool:
    """
    Pool of workers for parallel task execution
    
    Usage:
        pool = WorkerPool(num_workers=4, logger=logger)
        pool.start()
        
        pool.submit_task('task1', my_function, args=(arg1, arg2))
        pool.submit_task('task2', another_function, priority=TaskPriority.HIGH)
        
        pool.stop()
    """
    
    def __init__(self, num_workers: int, logger: logging.Logger):
        self.num_workers = num_workers
        self.logger = logger
        self.workers: list[BaseWorker] = []
        self._next_worker = 0
    
    def start(self):
        """Start all workers"""
        for i in range(self.num_workers):
            worker = BaseWorker(f"Worker-{i}", self.logger)
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Worker pool started with {self.num_workers} workers")
    
    def submit_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ):
        """Submit task to pool (round-robin distribution)"""
        if not self.workers:
            raise RuntimeError("Worker pool not started")
        
        # Get next worker (round-robin)
        worker = self.workers[self._next_worker]
        self._next_worker = (self._next_worker + 1) % self.num_workers
        
        # Add task to worker
        worker.add_task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            callback=callback,
            error_callback=error_callback
        )
    
    def stop(self):
        """Stop all workers"""
        self.logger.info("Stopping worker pool...")
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
        self.logger.info("Worker pool stopped")
    
    def get_stats(self) -> list[dict]:
        """Get statistics for all workers"""
        return [worker.get_stats() for worker in self.workers]
