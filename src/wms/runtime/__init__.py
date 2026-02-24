"""
Application Runtime System

This package provides the bootstrap and lifecycle management for the application.
"""

from .bootstrap import ApplicationBootstrap
from .lifecycle import ApplicationLifecycle

__all__ = ["ApplicationBootstrap", "ApplicationLifecycle"]
