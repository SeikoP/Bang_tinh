"""
Application Performance Profiler

Monitors and profiles application performance:
- Startup time tracking
- Memory usage monitoring
- CPU usage tracking
- Function execution profiling
- Performance bottleneck detection
"""

import functools
import logging
import threading
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class PerformanceMetric:
    """Single performance measurement"""

    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: Optional[int] = None
    memory_end: Optional[int] = None
    memory_delta: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, memory_end: Optional[int] = None):
        """Mark metric as finished"""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        if memory_end is not None and self.memory_start is not None:
            self.memory_end = memory_end
            self.memory_delta = memory_end - self.memory_start


class ApplicationProfiler:
    """
    Application performance profiler.

    Tracks startup time, memory usage, and function execution times.
    Useful for identifying performance bottlenecks.
    """

    def __init__(self, logger: logging.Logger, enabled: bool = True):
        self.logger = logger
        self.enabled = enabled
        self.metrics: List[PerformanceMetric] = []
        self.startup_time: Optional[float] = None
        self._memory_tracking = False
        self._lock = threading.Lock()  # Thread safety

        # Start memory tracking if available
        if self.enabled:
            try:
                if not tracemalloc.is_tracing():  # Prevent double start
                    tracemalloc.start()
                    self._memory_tracking = True
                    self.logger.debug("Memory tracking enabled")
            except Exception as e:
                self.logger.warning(f"Failed to start memory tracking: {e}")

    def start_metric(self, name: str, **metadata) -> PerformanceMetric:
        """
        Start tracking a performance metric.

        Args:
            name: Metric name
            **metadata: Additional metadata

        Returns:
            PerformanceMetric: The metric object
        """
        if not self.enabled:
            return PerformanceMetric(name=name, start_time=0)

        memory_start = None
        if self._memory_tracking:
            try:
                current, peak = tracemalloc.get_traced_memory()
                memory_start = current
            except:
                pass

        metric = PerformanceMetric(
            name=name,
            start_time=time.perf_counter(),
            memory_start=memory_start,
            metadata=metadata,
        )

        with self._lock:  # Thread-safe append
            self.metrics.append(metric)

        self.logger.debug(f"Started profiling: {name}")

        return metric

    def end_metric(self, metric: PerformanceMetric):
        """
        End tracking a performance metric.

        Args:
            metric: The metric to end
        """
        if not self.enabled or metric.end_time is not None:
            return

        memory_end = None
        if self._memory_tracking:
            try:
                current, peak = tracemalloc.get_traced_memory()
                memory_end = current
            except:
                pass

        metric.finish(memory_end)

        # Log the result
        msg = f"Profiling '{metric.name}': {metric.duration:.3f}s"
        if metric.memory_delta is not None:
            msg += f", Memory: {metric.memory_delta / 1024 / 1024:.2f} MB"

        self.logger.info(msg)

    def profile_function(self, name: Optional[str] = None):
        """
        Decorator to profile a function.

        Args:
            name: Optional custom name for the metric

        Example:
            @profiler.profile_function("database_init")
            def initialize_database():
                pass
        """

        def decorator(func: Callable) -> Callable:
            metric_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                metric = self.start_metric(metric_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.end_metric(metric)

            return wrapper

        return decorator

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics.

        Returns:
            Dict with CPU, memory, and disk metrics
        """
        metrics = {}

        if not HAS_PSUTIL:
            return metrics

        try:
            # CPU metrics
            metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            metrics["cpu_count"] = psutil.cpu_count()

            # Memory metrics
            mem = psutil.virtual_memory()
            metrics["memory_total"] = mem.total
            metrics["memory_available"] = mem.available
            metrics["memory_percent"] = mem.percent
            metrics["memory_used"] = mem.used

            # Disk metrics
            disk = psutil.disk_usage("/")
            metrics["disk_total"] = disk.total
            metrics["disk_used"] = disk.used
            metrics["disk_free"] = disk.free
            metrics["disk_percent"] = disk.percent

            # Process metrics
            process = psutil.Process()
            metrics["process_memory"] = process.memory_info().rss
            metrics["process_cpu_percent"] = process.cpu_percent()

        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")

        return metrics

    def log_system_metrics(self):
        """Log current system metrics"""
        metrics = self.get_system_metrics()

        if not metrics:
            return

        self.logger.info("System Metrics:")
        self.logger.info(f"  CPU: {metrics.get('cpu_percent', 0):.1f}%")
        self.logger.info(
            f"  Memory: {metrics.get('memory_percent', 0):.1f}% ({metrics.get('memory_used', 0) / 1024 / 1024 / 1024:.2f} GB)"
        )
        self.logger.info(
            f"  Disk: {metrics.get('disk_percent', 0):.1f}% ({metrics.get('disk_free', 0) / 1024 / 1024 / 1024:.2f} GB free)"
        )
        self.logger.info(
            f"  Process Memory: {metrics.get('process_memory', 0) / 1024 / 1024:.2f} MB"
        )

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate performance report.

        Args:
            output_path: Optional path to save report

        Returns:
            str: Report content
        """
        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("=" * 70)
        lines.append("")

        # Startup time
        if self.startup_time:
            lines.append(f"Startup Time: {self.startup_time:.3f}s")
            lines.append("")

        # System metrics
        metrics = self.get_system_metrics()
        if metrics:
            lines.append("System Metrics:")
            lines.append(f"  CPU: {metrics.get('cpu_percent', 0):.1f}%")
            lines.append(f"  Memory: {metrics.get('memory_percent', 0):.1f}%")
            lines.append(
                f"  Process Memory: {metrics.get('process_memory', 0) / 1024 / 1024:.2f} MB"
            )
            lines.append("")

        # Performance metrics
        if self.metrics:
            lines.append("Performance Metrics:")
            lines.append("")

            # Sort by duration
            sorted_metrics = sorted(
                self.metrics, key=lambda m: m.duration or 0, reverse=True
            )

            for metric in sorted_metrics:
                if metric.duration is None:
                    continue

                lines.append(f"  {metric.name}:")
                lines.append(f"    Duration: {metric.duration:.3f}s")

                if metric.memory_delta is not None:
                    lines.append(
                        f"    Memory: {metric.memory_delta / 1024 / 1024:.2f} MB"
                    )

                if metric.metadata:
                    lines.append(f"    Metadata: {metric.metadata}")

                lines.append("")

        report = "\n".join(lines)

        # Save to file if path provided
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(report, encoding="utf-8")
                self.logger.info(f"Performance report saved: {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save performance report: {e}")

        return report

    def cleanup(self):
        """Cleanup profiler resources"""
        if self._memory_tracking:
            try:
                if tracemalloc.is_tracing():  # Check before stopping
                    tracemalloc.stop()
                    self.logger.debug("Memory tracking stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping memory tracking: {e}")
