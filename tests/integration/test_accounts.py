import json
import datetime
import os
import requests
from decimal import Decimal
from florin import db
from florin.services.categories import INTERNAL_TRANSFER_CATEGORY_ID
from .utils import reset_database
from .fixtures.accounts import (td_chequing_account,
                                cibc_savings_account,
                                bmo_chequing_account,
                                tangerine_credit_card_account,
                                rogers_bank_credit_card_account)
from .fixtures.categories import automobile, gasoline, insurance, mortgage, salary
from .fixtures.transactions import create


def setup_function(function):
    reset_database()


def test_accounts_get___empty():
    response = requests.get('http://localhost:7000/api/accounts')
    assert response.json() == {'accounts': []}


def test_accounts_get___one_account(td_chequing_account):
    response = requests.get('http://localhost:7000/api/accounts')
    assert response.json() == {
        'accounts': [
            td_chequing_account
        ]}


def test_accounts_get___ordered_by_institution_name_by_default(td_chequing_account,
                                                               cibc_savings_account,
                                                               bmo_chequing_account):
    response = requests.get('http://localhost:7000/api/accounts')
    names = [r['institution'] for r in response.json()['accounts']]
    assert names == ['TD', 'CIBC', 'BMO']


def test_accounts_upload___file_extension_not_supported(tangerine_credit_card_account):
    response = requests.post('http://localhost:7000/api/accounts/4/upload', files=[
        ('requirements.txt', ('requirements.txt', open('requirements.txt', 'r'), 'text/plain'))
    ])
    assert response.status_code == 400
    assert response.json() == {'error': 'Unsupported file extension'}


def assert_transaction(transaction, expected_dict):
    for key, value in expected_dict.items():
        assert getattr(transaction, key) == value


def test_accounts_upload___csv___tangerine(tangerine_credit_card_account):
    response = requests.post('http://localhost:7000/api/accounts/4/upload', files=[
        ('tangerine.csv', ('tangerine.csv', open(os.path.join(
            os.path.dirname(__file__), 'fixtures/tangerine.csv'), 'r'), 'text/csv'))
    ])
    assert response.status_code == 200
    assert response.json() == {'totalImported': 2, 'totalSkipped': 0}

    transactions = db.Transaction.session.query(db.Transaction).all()
    assert len(transactions) == 2
    assert_transaction(transactions[0],
                        {
                            'info': 'Completed transfer to Tangerine DDA account XXXXXXXXXXXX~ Internet Withdrawal',
                            'account_id': 4,
                            "transaction_type": "debit",
                            'payee': 'Internet Withdrawal to Tangerine',
                            'amount': Decimal('-1000.00'),
                            'date': datetime.date(2017, 3, 7),
                            'category_id': 65535,
                        })
    assert_transaction(transactions[1],
                        {'info': 'From FOOINC.COM INC',
                        'account_id': 4,
                        'amount': Decimal('3000.00'),
                        'date': datetime.date(2017, 3, 14),
                        'category_id': 65535
                        })


def test_accounts_upload___csv___tangerine___skip_duplicates(tangerine_credit_card_account):
    response = requests.post('http://localhost:7000/api/accounts/4/upload', files=[
        ('tangerine.csv', ('tangerine.csv', open(os.path.join(
            os.path.dirname(__file__), 'fixtures/tangerine.csv'), 'r'), 'text/csv'))
    ])
    assert response.status_code == 200
    assert response.json() == {'totalImported': 2, 'totalSkipped': 0}

    response = requests.post('http://localhost:7000/api/accounts/4/upload', files=[
        ('tangerine.csv', ('tangerine.csv', open(os.path.join(
            os.path.dirname(__file__), 'fixtures/tangerine.csv'), 'r'), 'text/csv'))
    ])
    assert response.status_code == 200
    assert response.json() == {'totalImported': 0, 'totalSkipped': 2}


def test_accounts_upload___ofx(tangerine_credit_card_account):
    response = requests.post('http://localhost:7000/api/accounts/4/upload', files=[
        ('reports.ofx', ('reports.ofx', open(os.path.join(
            os.path.dirname(__file__), 'fixtures/reports.ofx'), 'r'), 'application/ofx'))
    ])
    assert response.status_code == 200

    txns = db.Transaction.session.query(db.Transaction).all()
    assert 6 == len(txns)
    account_balances = db.AccountBalance.session.query(db.AccountBalance).all()
    assert 1 == len(account_balances)
    assert 2935.4 == account_balances[0].balance


def test_accounts_new():
    response = requests.post('http://localhost:7000/api/accounts',
                             headers={'content-type': 'application/json'},
                             data=json.dumps({
                                 'account': {
                                     'institution': 'BAH',
                                     'name': 'DOH',
                                     'type': 'chequing',
                                 }
                             }))
    assert response.status_code == 201
    response_json = response.json()
    assert response_json['account']['institution'] == 'BAH'
    assert response_json['account']['name'] == 'DOH'
    assert response_json['account']['type'] == 'chequing'


def test_accounts_get_category_summary___empty_account():
    response = requests.get('http://localhost:7000/api/accounts/_all/categorySummary')
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['categorySummary'] == {'expense': [], 'income': []}


def test_accounts_get_category_summary(tangerine_credit_card_account,
                                       td_chequing_account,
                                       automobile,
                                       gasoline,
                                       insurance,
                                       mortgage,
                                       salary):
    create(account_id=tangerine_credit_card_account['id'], category_id=automobile['id'],
           transaction_type='debit', amount=Decimal('10'))
    create(account_id=tangerine_credit_card_account['id'], category_id=automobile['id'],
           transaction_type='debit', amount=Decimal('20'))
    create(account_id=tangerine_credit_card_account['id'], category_id=gasoline['id'],
           transaction_type='debit', amount=Decimal('30'))
    create(account_id=tangerine_credit_card_account['id'], category_id=insurance['id'],
           transaction_type='debit', amount=Decimal('60'))
    create(account_id=td_chequing_account['id'], category_id=mortgage['id'],
           transaction_type='debit', amount=Decimal('600'))
    create(account_id=td_chequing_account['id'], category_id=salary['id'],
           transaction_type='credit', amount=Decimal('1500'))
    create(account_id=td_chequing_account['id'], category_id=INTERNAL_TRANSFER_CATEGORY_ID,
           transaction_type='other', amount=Decimal('2500'))


    response = requests.get('http://localhost:7000/api/accounts/_all/categorySummary')
    assert response.status_code == 200
    response_json = response.json()

    expected_income = [
        {
            'category_id': salary['id'],
            'category_name': salary['name'],
            'amount': 1500,
        }
    ]
    expected_expense = [
        {
            'category_id': mortgage['id'],
            'category_name': mortgage['name'],
            'amount': 600,
        },
        {
            'category_id': automobile['id'],
            'category_name': automobile['name'],
            'amount': 120,
        }
    ]
    assert response_json['categorySummary']['income'] == expected_income
    assert response_json['categorySummary']['expense'] == expected_expense
