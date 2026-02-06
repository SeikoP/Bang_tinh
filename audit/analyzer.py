"""
Base analyzer class for code analysis.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class CodeAnalyzer(ABC):
    """Base class for code analyzers with file discovery."""

    def __init__(self, project_root: Path):
        """
        Initialize analyzer with project root.

        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root)
        self.python_files: List[Path] = []

    def discover_files(self, exclude_patterns: List[str] = None) -> List[Path]:
        """
        Discover all Python source files in the project.

        Args:
            exclude_patterns: List of patterns to exclude (e.g., ['venv', '__pycache__', 'tests'])

        Returns:
            List of Path objects for discovered Python files
        """
        if exclude_patterns is None:
            exclude_patterns = ["venv", "__pycache__", ".git", "build", "dist"]

        python_files = []

        for py_file in self.project_root.rglob("*.py"):
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern in str(py_file):
                    should_exclude = True
                    break

            if not should_exclude:
                python_files.append(py_file)

        self.python_files = python_files
        return python_files

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Perform analysis on discovered files.

        Returns:
            Dictionary containing analysis results
        """
        pass

    def get_file_content(self, file_path: Path) -> str:
        """
        Read and return file content.

        Args:
            file_path: Path to the file

        Returns:
            File content as string
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"
