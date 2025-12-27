import os
import sys
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ---- тестова база ----
os.environ["DATABASE_URL"] = "sqlite:///test.db"

from app.app import app
from app import database


@pytest.fixture
def client():
    app.config["TESTING"] = True

    # створюємо БД перед тестами
    database.init_db()

    with app.test_client() as client:
        yield client
