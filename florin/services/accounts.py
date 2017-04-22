import datetime
import operator
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from .exceptions import ResourceNotFound, InvalidRequest
from . import params
from florin.db import Account, AccountBalance, Transaction, Category
from sqlalchemy import func, and_, not_


ALL_ACCOUNTS = object()


def get_balances(app, account_id):
    if account_id != '_all':
        raise InvalidRequest('Currently only "_all" is supported for account_id')
    accounts = Account.query().filter(not_(Account.deleted)).all()
    return {
        'accountBalances': [
            account.to_dict(extra_fields=['balances']) for account in accounts
        ]
    }


def post_balances(app, account_id, request_json):
    if account_id == '_all':
        raise InvalidRequest('Invalid account_id')

    account = get_by_id(app, account_id)

    date = request_json.get('date')
    if date is None:
        raise InvalidRequest("Invalid field 'date'")
    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise InvalidRequest("Invalid field 'date'")

    balance = request_json.get('balance')
    if balance is None:
        raise InvalidRequest("Invalid field 'balance'")
    try:
        balance = Decimal(balance)
    except InvalidOperation:
        raise InvalidRequest("Invalid field 'balance'")

    account_balance = AccountBalance(account_id=account_id, date=date, balance=balance)
    app.session.add(account_balance)
    try:
        app.session.commit()
    except:
        app.session.rollback()
        raise
    else:
        return {'account_id': account_id, 'id': account_balance.id}


def get_by_id(app, account_id):
    if account_id == '_all':
        return ALL_ACCOUNTS

    query = app.session.query(Account).filter(and_(
        not_(Account.deleted), Account.id == account_id))
    if query.count() != 1:
        raise ResourceNotFound()

    return query.one()


def _get_expense_category_summary(app, args):
    start_date, end_date = params.get_date_range_params(args)
    session = app.session
    query = (
        session.query(Category.id, Category.parent_id, Category.name, func.sum(Transaction.amount).label('amount'))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(and_(Transaction.date >= start_date, Transaction.date <= end_date))
        .filter(Category.type == 'expense')
        .filter(not_(Transaction.deleted))
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


def _get_income_category_summary(app, args):
    start_date, end_date = params.get_date_range_params(args)
    session = app.session
    query = (
        session.query(Category.id, Category.name, func.sum(Transaction.amount))
        .filter(and_(Transaction.date >= start_date, Transaction.date <= end_date))
        .filter(Transaction.category_id == Category.id)
        .filter(Category.type == 'income')
        .filter(not_(Transaction.deleted))
        .group_by(Category.id)
    )

    return [
        {'category_id': category_id, 'category_name': category_name, 'amount': abs(amount)}
        for category_id, category_name, amount in query.all()
    ]


def get_summary(app, account_id, args):
    return {
        'categorySummary': {
            'expense': _get_expense_category_summary(app, args),
            'income': _get_income_category_summary(app, args)
        }
    }


def get(app):
    query = app.session.query(Account) \
        .filter(not_(Account.deleted)) \
        .order_by(Account.institution.desc())  # TODO: why desc?
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


def put(app, account_id, request_json):
    account = get_by_id(app, account_id)
    session = app.session
    try:
        for key, value in request_json['account'].items():
            setattr(account, key, value)
        session.add(account)
        session.commit()
    except Exception as e:
        session.rollback()
        raise InvalidRequest(str(e))
    else:
        account_id = account.id
        account = get_by_id(app, account_id)
        return {'account': account.to_dict()}


def delete(app, account_id):
    account = get_by_id(app, account_id)
    session = app.session
    account.deleted = True

    for t in account.transactions:
        t.deleted = True
        session.add(t)

    session.add(account)
    try:
        session.commit()
    except:
        session.rollback()
        raise
    else:
        return {'accountId': account_id}
