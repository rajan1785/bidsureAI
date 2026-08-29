import os
import sys
import tempfile
from pathlib import Path

os.environ["COMPLYGEM_DB"] = str(Path(tempfile.mkdtemp()) / "test.db")
sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest

from app.db import SessionLocal, init_db


@pytest.fixture()
def db():
    init_db()
    s = SessionLocal()
    yield s
    s.close()
