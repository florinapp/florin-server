import operator
from florin.importer import get_importer
from collections import defaultdict
from .exceptions import ResourceNotFound, InvalidRequest
from .categories import TBD_CATEGORY_ID
from . import params
from florin.db import Account, AccountBalance, Transaction, Category
from sqlalchemy import func, and_


ALL_ACCOUNTS = object()


def get_by_id(app, account_id):
    if account_id == '_all':
        return ALL_ACCOUNTS

    query = app.session.query(Account).filter(Account.id == account_id)
    if query.count() != 1:
        raise ResourceNotFound()

    return query.one()


def _get_expense_category_summary(app, account_id, args):
    start_date, end_date = params.get_date_range_params(args)
    session = app.session
    query = (
        session.query(Category.id, Category.parent_id, Category.name, func.sum(Transaction.amount).label('amount'))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(and_(Transaction.date >= start_date, Transaction.date <= end_date))
        .filter(Category.type == 'expense')
        .group_by(Category.id)
    )

    result = query.all()

    def reducer(aggregate, (id, parent_id, name, amount)):
        if parent_id is None:
            aggregate[id] += amount
        else:
            aggregate[parent_id] += amount
        return aggregate

    result = reduce(reducer, result, defaultdict(float))

    return [
        {'category_id': id, 'category_name': Category.get_by_id(id).name, 'amount': abs(amount)}
        for id, amount in reversed(sorted(result.items(), key=operator.itemgetter(1)))
    ]


def _get_income_category_summary(app, account_id, args):
    start_date, end_date = params.get_date_range_params(args)
    session = app.session
    query = session.query(Category.id, Category.name, func.sum(Transaction.amount))
    query = query.filter(and_(Transaction.date >= start_date,
                              Transaction.date <= end_date))
    query = query.filter(Transaction.category_id == Category.id)
    query = query.filter(Category.type == 'income')
    query = query.group_by(Category.id)

    return [
        {'category_id': category_id, 'category_name': category_name, 'amount': abs(amount)}
        for category_id, category_name, amount in query.all()
    ]


def get_summary(app, account_id, args):
    return {
        'categorySummary': {
            'expense': _get_expense_category_summary(app, account_id, args),
            'income': _get_income_category_summary(app, account_id, args)
        }
    }


def get(app):
    query = app.session.query(Account).order_by(Account.institution.desc())  # TODO: why desc?
    accounts = query.all()
    return {
        'accounts': [account.to_dict() for account in accounts]
    }


def post(app, request_json):
    session = app.session
    try:
        request_json['account']['id'] = None
        account = Account(**request_json['account'])
        session.add(account)
        session.commit()
    except Exception as e:
        session.rollback()
        raise InvalidRequest(str(e))
    else:
        account_id = account.id
        account = get_by_id(app, account_id)
        return {'account': account.to_dict()}


def upload(app, account_id, files):
    session = app.session
    file_items = files.items()
    assert len(file_items) == 1
    filename, file_storage = file_items[0]
    importer = get_importer(filename)
    if not importer:
        raise InvalidRequest('Unsupported file extension')

    transactions, balance = importer.import_from(file_storage)
    total_imported, total_skipped = 0, 0

    account = get_by_id(app, account_id)
    for t in transactions:
        common_attrs = dict(t.common_attrs)
        common_attrs['account_id'] = account.id  # TODO: Use relationship
        common_attrs['category_id'] = TBD_CATEGORY_ID
        try:
            session.add(Transaction(**common_attrs))
            session.commit()
        except Exception as e:
            print(str(e))
            session.rollback()
            total_skipped += 1
        else:
            total_imported += 1

    if balance is not None:
        balance.update({
            'account_id': account.id,
        })
        account_balance = AccountBalance(**balance)
        session.add(account_balance)
        try:
            session.commit()
        except:
            session.rollback()
            raise

    return {
        'totalImported': total_imported,
        'totalSkipped': total_skipped
    }
