"""
Compatibility layer for medias views

This file maintains backward compatibility by importing all views from the views/ directory.
This ensures existing imports like 'from medias.views import ProjectDocPDFS' continue to work.
"""

from .views import *  # noqa: F401, F403
