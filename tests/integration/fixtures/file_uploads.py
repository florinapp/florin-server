import datetime
import base64
import os
import pytest
from florin import db
from ..utils import db_fixture


@pytest.fixture
@db_fixture(db.FileUpload)
def td_ofx():
    fixture_path = os.path.join(os.path.dirname(__file__), 'reports.ofx')
    with open(fixture_path, 'r') as fh:
        file_content = fh.read()

    return dict(
        id=1,
        filename='foo.ofx',
        uploaded_at=datetime.datetime.utcnow(),
        file_content=base64.b64encode(file_content)
    )
