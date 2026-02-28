"""
Second-Me: Personal AI Self-Training System
L0/L1/L2 Hierarchical Memory Pipeline
"""

__version__ = "2.0.0"
__author__ = "Michael Lefebvre"

from .L0 import data_processor
from .L1 import memory_synthesizer
from .L2 import model_finetuner

__all__ = [
    "data_processor",
    "memory_synthesizer",
    "model_finetuner"
]
