import base64
import os
import requests
from florin import db


def test_uploads():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/file_uploads', files=[
        ('reports.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx'))
    ])
    assert response.status_code == 200
    id = response.json()['id']
    file_upload = db.FileUpload.get_by_id(id)
    assert file_upload.filename == 'reports.ofx'
    assert file_upload.file_content == base64.b64encode(open(fixture_path, 'r').read())


def test_uploads___cannot_upload_more_than_one_file_at_a_time():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/file_uploads', files=[
        ('reports.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx')),
        ('another.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx')),
    ])
    assert response.status_code == 400
    assert response.json() == {'error': 'Only one file can be uploaded at a time'}


def test_uploads___wrong_file_extension():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/file_uploads', files=[
        ('reports.duh', ('reports.ofx', open(fixture_path, 'r'), 'text/plain')),
    ])
    assert response.status_code == 400
    assert response.json() == {'error': 'Only .OFX and .QFX files are supported at this time'}
