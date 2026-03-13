# scripts/tests/conftest.py
"""Add scripts/ to sys.path so run_campaign is importable as a module."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
