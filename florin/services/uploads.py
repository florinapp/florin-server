import logging
import hashlib
import base64
import datetime
from .exceptions import InvalidRequest, ResourceNotFound
from florin.db import FileUpload, Transaction, Account, AccountBalance
from ofxparse import OfxParser
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from StringIO import StringIO
from .categories import TBD_CATEGORY_ID


logger = logging.getLogger(__name__)


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
    ofxfile = parser.parse(file_storage)
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


def link(app, file_upload_id, request_json):
    session = app.session
    try:
        file_upload = FileUpload.get_by_id(file_upload_id)
    except NoResultFound:
        raise ResourceNotFound()

    if file_upload.account_id is not None:
        raise InvalidRequest('file_upload {} is already associated with an account'.format(file_upload_id))

    account_id = request_json['accountId']
    if account_id == 'NEW':
        account = Account(
            institution='Unnamed',
            name='Unnamed',
            type='N/A',
        )
        session.add(account)
        try:
            session.commit()
        except:
            session.rollback()
            raise
    else:
        try:
            account = Account.get_by_id(account_id)
        except NoResultFound:
            raise InvalidRequest('Invalid account_id: {}'.format(account_id))

    file_content = base64.b64decode(file_upload.file_content)
    parser = OfxParser()
    ofxfile = parser.parse(StringIO(file_content))

    total_imported, total_skipped = 0, 0
    for t in ofxfile.account.statement.transactions:
        transaction = Transaction(date=t.date,
                                  info=t.memo,
                                  payee=t.payee,
                                  memo=t.memo,
                                  amount=t.amount,
                                  transaction_type=t.type,
                                  category_id=TBD_CATEGORY_ID,
                                  account_id=account.id)
        session.add(transaction)
        try:
            session.commit()
            total_imported += 1
        except IntegrityError:
            session.rollback()
            total_skipped += 1
            logger.warn('Skip duplicated transaction: {}. checksum: {}'.format(transaction, transaction.checksum))

    file_upload.account_id = account.id
    # record account balance history
    account_balance = AccountBalance(
        account_id=account.id,
        date=ofxfile.account.statement.balance_date,
        balance=ofxfile.account.statement.balance
    )
    session.add(file_upload)
    session.add(account_balance)
    try:
        session.commit()
    except IntegrityError:
        logger.info('Already a record of account balance for account {} on {}'.format(account_balance.account_id,
                                                                                      account_balance.date))
        session.rollback()
    except:
        session.rollback()
        raise

    return {'account_id': account.id, 'total_imported': total_imported, 'total_skipped': total_skipped}
