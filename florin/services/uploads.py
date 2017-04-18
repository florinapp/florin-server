import hashlib
import base64
import datetime
from .exceptions import InvalidRequest
from florin.db import FileUpload
from ofxparse import OfxParser


def ensure_single_file_uploaded(files):
    file_items = files.items()
    if len(file_items) != 1:
        raise InvalidRequest('Only one file can be uploaded at a time')
    return file_items


def ensure_file_extension(filename):
    filename = filename.lower()
    if filename.endswith('ofx') or filename.endswith('qfx'):
        return
    raise InvalidRequest('Only .OFX and .QFX files are supported at this time')


def calculate_account_signature(ofx_account):
    """A signature that somewhat uniquely identifies an OFX file with an account"""
    fields = ['account_id', 'account_type', 'branch_id', 'curdef', 'institution',
              'number', 'routing_number', 'type']

    return 'sha256:' + hashlib.sha256('&'.join([str(getattr(ofx_account, field)) for field in fields])).hexdigest()


def upload(app, files):
    session = app.session
    file_items = ensure_single_file_uploaded(files)
    filename, file_storage = file_items[0]
    ensure_file_extension(filename)

    parser = OfxParser()
    ofxfile= parser.parse(file_storage)
    account_signature = calculate_account_signature(ofxfile.account)

    file_storage.seek(0)
    file_upload = FileUpload(filename=filename, uploaded_at=datetime.datetime.utcnow(),
                             file_content=base64.b64encode(file_storage.read()),
                             account_signature=account_signature)

    session.add(file_upload)
    try:
        session.commit()
    except:
        session.rollback()
        raise

    # TODO: match an existing account and return the account_id
    return {'id': file_upload.id, 'signature': account_signature}
