from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from paylater.main import create_app
from paylater.settings import Settings

NOW = datetime(2026, 1, 31, 9, 30)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(database_url="sqlite+pysqlite:///:memory:"), clock=lambda: NOW)
    with TestClient(app) as http:
        yield http
