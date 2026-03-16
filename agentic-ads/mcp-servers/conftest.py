import sys
import os

# Add mcp-servers directory to sys.path so tests can import modules without hyphen issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
