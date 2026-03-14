"""
Configuration pytest
"""
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_config():
    """Configuration pour les tests"""
    return {
        "database_url": "sqlite:///:memory:",
        "secret_key": "test-secret-key",
        "debug": True
    }
