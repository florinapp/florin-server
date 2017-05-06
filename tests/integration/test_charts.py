import requests
import datetime
from decimal import Decimal
from florin.db import Account, AccountBalance
from .utils import reset_database
from .fixtures.transactions import create, fake
from .fixtures.accounts import *  # noqa


def setup_function(function):
    reset_database()


def test_get_account_balance_chart_data___only_balance_record(tangerine_credit_card_account):
    session = AccountBalance.session
    session.add(
        AccountBalance(
            account_id=tangerine_credit_card_account['id'],
            date=fake.date_time_between_dates(
                datetime_start=datetime.datetime(2017, 1, 1),
                datetime_end=datetime.datetime(2017, 2, 28)
            ).date(),
            balance=Decimal('150.00')
        ))
    session.add(
        AccountBalance(
            account_id=tangerine_credit_card_account['id'],
            date=fake.date_time_between_dates(
                datetime_start=datetime.datetime(2017, 3, 1),
                datetime_end=datetime.datetime(2017, 3, 31)
            ).date(),
            balance=Decimal('200.00')
        ))
    session.commit()

    response = requests.get('http://localhost:7000/api/charts/accountBalances')
    assert response.status_code == 200
    chart_data = response.json()['chartData']
    assert len(chart_data) == 1
    assert chart_data[0]['account']['id'] == tangerine_credit_card_account['id']
    assert len(chart_data[0]['history']) == 2
    assert [h['balance'] for h in chart_data[0]['history']] == [150, 200]


def test_get_account_balance_chart_data___infer_with_transactions():
    session = AccountBalance.session
    account = Account(
        institution='TEST BANK',
        name='TEST ACCT',
        type='credit',
        balances=[
            AccountBalance(
                date=datetime.datetime(2017, 2, 28).date(),
                balance=Decimal('150.00'))
        ],
    )
    session.add(account)
    session.commit()
    create(date=datetime.datetime(2017, 2, 28),
           amount=Decimal('-50'),
           account_id=account.id,
           transaction_type='debit')
    create(date=datetime.datetime(2017, 2, 28),
           amount=Decimal('-20'),
           account_id=account.id,
           transaction_type='debit')
    response = requests.get('http://localhost:7000/api/charts/accountBalances')
    assert response.status_code == 200
    chart_history = response.json()['chartData'][0]['history']
    actual = [{'date': h['date'], 'balance': h['balance']}
              for h in chart_history]
    assert actual == [
        {'date': '2017-02-27', 'balance': 220},
        {'date': '2017-02-28', 'balance': 150},
    ]
