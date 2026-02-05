"""
Application Runtime System

This package provides the bootstrap and lifecycle management for the application.
"""

from runtime.bootstrap import ApplicationBootstrap
from runtime.lifecycle import ApplicationLifecycle

__all__ = ['ApplicationBootstrap', 'ApplicationLifecycle']
