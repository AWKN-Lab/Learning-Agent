import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_fd, TEST_DB = tempfile.mkstemp(
    prefix="learning-agent-pytest-",
    suffix=".db",
)
os.close(_fd)
os.environ["LEARNING_DB_PATH"] = TEST_DB
os.environ["APP_ENV"] = "test"


@pytest.fixture
def client():
    from apps.api.app import app

    return TestClient(app)
