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
