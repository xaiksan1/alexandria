import sys
import os
import warnings
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Vault emits RuntimeWarning in tests when VAULT_MNEMONIC is not set — expected
warnings.filterwarnings("ignore", category=RuntimeWarning, message="VAULT_MNEMONIC not set")


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
