import logging
import hashlib
import base64
import datetime
from .exceptions import InvalidRequest, ResourceNotFound
from florin.db import FileUpload, Transaction, Account, AccountBalance, db_transaction
from ofxparse import OfxParser
from sqlalchemy import func
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

    with db_transaction(session):
        session.add(file_upload)

    query = (
        FileUpload.query().with_entities(FileUpload.account_id, func.count(FileUpload.id))
        .filter(FileUpload.account_id != None)  # noqa
        .group_by(FileUpload.account_id)
        .order_by(func.count(FileUpload.id).desc())
    )
    result = query.all()
    if not result:
        link = {
            'accountId': None,
            'confidenceIndex': None
        }
    else:
        account_id = result[0][0]
        confidence_index = 1.0 * result[0][1] / sum([r[1] for r in result])
        link = {
            'accountId': account_id,
            'confidenceIndex': confidence_index
        }

    return {
        'id': file_upload.id,
        'signature': account_signature,
        'link': link,
    }


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
        with db_transaction(session):
            session.add(account)
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
        try:
            with db_transaction(session):
                session.add(transaction)
                total_imported += 1
        except IntegrityError:
            total_skipped += 1
            logger.warn('Skip duplicated transaction: {}. checksum: {}'.format(transaction, transaction.checksum))

    file_upload.account_id = account.id
    # record account balance history
    account_balance = AccountBalance(
        account_id=account.id,
        date=ofxfile.account.statement.balance_date,
        balance=ofxfile.account.statement.balance
    )

    try:
        with db_transaction(session):
            session.add(file_upload)
            session.add(account_balance)
    except IntegrityError:
        logger.info('Already a record of account balance for account {} on {}'.format(account_balance.account_id,
                                                                                      account_balance.date))

    return {'account_id': account.id, 'total_imported': total_imported, 'total_skipped': total_skipped}
