import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use test database
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_platform.db")


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    """Initialize test database before tests run."""
    from backend.database.db import init_db
    init_db()
    yield
    # Cleanup
    if os.path.exists("test_platform.db"):
        os.remove("test_platform.db")
    if os.path.exists("test_integration.db"):
        os.remove("test_integration.db")
