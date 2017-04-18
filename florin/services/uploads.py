import base64
import datetime
from .exceptions import InvalidRequest
from florin.db import FileUpload


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


def upload(app, files):
    session = app.session
    file_items = ensure_single_file_uploaded(files)
    filename, file_storage = file_items[0]
    ensure_file_extension(filename)

    file_upload = FileUpload(filename=filename, uploaded_at=datetime.datetime.utcnow(),
                             file_content=base64.b64encode(file_storage.read()))
    session.add(file_upload)
    try:
        session.commit()
    except:
        session.rollback()
        raise

    return {'id': file_upload.id}
