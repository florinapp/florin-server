import json
import base64
import os
import requests
from florin import db
from .utils import reset_database
from .fixtures.accounts import td_chequing_account
from .fixtures.file_uploads import td_ofx


def setup_function(function):
    reset_database()


def test_uploads():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/fileUploads', files=[
        ('reports.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx'))
    ])
    assert response.status_code == 200
    id = response.json()['id']
    file_upload = db.FileUpload.get_by_id(id)
    assert file_upload.filename == 'reports.ofx'
    assert file_upload.file_content == base64.b64encode(open(fixture_path, 'r').read())


def test_uploads___cannot_upload_more_than_one_file_at_a_time():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/fileUploads', files=[
        ('reports.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx')),
        ('another.ofx', ('reports.ofx', open(fixture_path, 'r'), 'application/ofx')),
    ])
    assert response.status_code == 400
    assert response.json() == {'error': 'Only one file can be uploaded at a time'}


def test_uploads___wrong_file_extension():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/reports.ofx')
    response = requests.post('http://localhost:7000/api/fileUploads', files=[
        ('reports.duh', ('reports.ofx', open(fixture_path, 'r'), 'text/plain')),
    ])
    assert response.status_code == 400
    assert response.json() == {'error': 'Only .OFX and .QFX files are supported at this time'}


def test_link_upload_with_account___wrong_account_id(td_ofx):
    response = requests.post('http://localhost:7000/api/fileUploads/{}/linkAccount'.format(td_ofx['id']),
                             headers={'content-type': 'application/json'},
                             data=json.dumps({'accountId': 999}))
    assert response.status_code == 400
    assert response.json() == {'error': 'Invalid account_id: 999'}


def test_link_upload_with_account___wrong_upload_id(td_chequing_account):
    response = requests.post('http://localhost:7000/api/fileUploads/999/linkAccount',
                             headers={'content-type': 'application/json'},
                             data=json.dumps({'accountId': td_chequing_account['id']}))
    assert response.status_code == 404


def test_link_upload_with_account___upload_already_linked(td_chequing_account, td_ofx):
    session = db.Account.session
    account = db.Account.get_by_id(td_chequing_account['id'])
    file_upload = db.FileUpload.get_by_id(td_ofx['id'])
    file_upload.account_id = account.id
    session.add(file_upload)
    session.commit()

    response = requests.post('http://localhost:7000/api/fileUploads/{}/linkAccount'.format(file_upload.id),
                             headers={'content-type': 'application/json'},
                             data=json.dumps({'accountId': account.id}))
    assert response.status_code == 400
    assert {'error': 'file_upload 1 is already associated with an account'} == response.json()


def test_link_upload_with_account(td_chequing_account, td_ofx):
    session = db.Account.session
    account = db.Account.get_by_id(td_chequing_account['id'])
    file_upload = db.FileUpload.get_by_id(td_ofx['id'])

    response = requests.post('http://localhost:7000/api/fileUploads/{}/linkAccount'.format(file_upload.id),
                             headers={'content-type': 'application/json'},
                             data=json.dumps({'accountId': account.id}))
    assert response.status_code == 200
    assert response.json() == {'total_skipped': 0, 'total_imported': 6, 'account_id': account.id}
    assert account.balances[0].balance == 2935.4

    session.expunge_all()
    file_upload = db.FileUpload.get_by_id(file_upload.id)
    assert file_upload.account_id == account.id


def test_link_upload_with_account___create_new_account():
    pass
