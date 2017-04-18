import json
import datetime
import requests
from florin import db
from .utils import reset_database
from .fixtures.transactions import create, fake
from .fixtures.accounts import tangerine_credit_card_account, rogers_bank_credit_card_account


def setup_function(function):
    reset_database()


def test_transactions_get___empty():
    response = requests.get('http://localhost:7000/api/accounts/_all')
    assert response.status_code == 200
    assert response.json() == {'transactions': [], 'total_pages': 0, 'current_page': 1}


def test_transactions_get___tangerine_account(tangerine_credit_card_account):  # noqa
    for _ in xrange(5):
        create(account_id=tangerine_credit_card_account['id'])
    response = requests.get('http://localhost:7000/api/accounts/4')
    assert response.status_code == 200
    response_json = response.json()
    assert 5 == len(response_json['transactions'])
    assert response_json['current_page'] == 1
    assert response_json['total_pages'] == 1


def test_transactions_get___pagination(tangerine_credit_card_account):  # noqa
    for _ in xrange(5):
        create(account_id=tangerine_credit_card_account['id'])
    response = requests.get('http://localhost:7000/api/accounts/4?perPage=4&page=1')
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['current_page'] == 1
    assert response_json['total_pages'] == 2


def test_transactions_get___pagination___edge_case(tangerine_credit_card_account):  # noqa
    for _ in xrange(6):
        create(account_id=tangerine_credit_card_account['id'])
    response = requests.get('http://localhost:7000/api/accounts/4?perPage=2&page=3')
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['current_page'] == 3
    assert response_json['total_pages'] == 3


def test_transactions_get___transactions_from_multiple_accounts_are_available_under_all(  # noqa
        tangerine_credit_card_account, rogers_bank_credit_card_account):
    for _ in xrange(5):
        create(account_id=tangerine_credit_card_account['id'])
    for _ in xrange(5):
        create(account_id=rogers_bank_credit_card_account['id'])
    response = requests.get('http://localhost:7000/api/accounts/_all')
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['total_pages'] == 1
    assert response_json['current_page'] == 1


def test_transactions_get___transactions_in_date_range(tangerine_credit_card_account):  # noqa
    # before startDate
    for _ in xrange(2):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())
    # between startDate and endDate
    for _ in xrange(3):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 3, 1),
                   datetime_end=datetime.datetime(2017, 3, 13)).date())
    # on endDate
    create(account_id=tangerine_credit_card_account['id'], date=datetime.date(2017, 3, 13))
    for _ in xrange(3):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 3, 14),
                   datetime_end=datetime.datetime(2017, 3, 31)).date())
    response = requests.get('http://localhost:7000/api/accounts/_all?'
                            'startDate=2017-03-01&endDate=2017-03-13')
    assert response.status_code == 200
    response_json = response.json()
    assert 4 == len(response_json['transactions'])


def test_transactions_get___invalid_order_by_param___invalid_direction(tangerine_credit_card_account):  # noqa
    for _ in xrange(10):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())

    response = requests.get('http://localhost:7000/api/accounts/_all?orderBy=date:ascd')
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid orderBy param: "date:ascd"'


def test_transactions_get___invalid_order_by_param___invalid_column(tangerine_credit_card_account):  # noqa
    for _ in xrange(10):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())

    response = requests.get('http://localhost:7000/api/accounts/_all?orderBy=datez:asc')
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid orderBy param: "datez:asc"'


def test_transactions_get___order_by_date_asc(tangerine_credit_card_account):  # noqa
    for _ in xrange(10):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())

    response = requests.get('http://localhost:7000/api/accounts/_all?orderBy=date:asc')
    assert response.status_code == 200
    response_json = response.json()
    dates = [r['date'] for r in response_json['transactions']]
    assert dates == sorted(dates)


def test_transactions_get___order_by_date_desc(tangerine_credit_card_account):  # noqa
    for _ in xrange(10):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())

    response = requests.get('http://localhost:7000/api/accounts/_all?orderBy=date:desc')
    assert response.status_code == 200
    response_json = response.json()
    dates = [r['date'] for r in response_json['transactions']]
    assert dates == list(reversed(sorted(dates)))


def test_transactions_delete(tangerine_credit_card_account):
    for _ in xrange(10):
        create(account_id=tangerine_credit_card_account['id'],
               date=fake.date_time_between_dates(
                   datetime_start=datetime.datetime(2017, 1, 1),
                   datetime_end=datetime.datetime(2017, 2, 28)).date())
    txns = db.Transaction.session.query(db.Transaction).all()
    assert 10 == len(txns)
    response = requests.delete('http://localhost:7000/api/transactions/{}'.format(txns[0].id))
    assert response.status_code == 200
    assert 9 == db.Transaction.session.query(db.Transaction).count()


def test_transactions_put___change_memo(tangerine_credit_card_account):
    create(account_id=tangerine_credit_card_account['id'])
    txn_before = db.Transaction.session.query(db.Transaction).first()
    response = requests.put('http://localhost:7000/api/transactions/{}'.format(txn_before.id),
                            headers={'content-type': 'application/json'},
                            data=json.dumps({
                                'memo': 'XYZ'
                            }))
    assert response.status_code == 200
    assert response.json()['transactions'][0]['memo'] == 'XYZ'


# TODO: order by category name
# def test_transactions_get___order_by_category_name(tangerine_credit_card_account,               # noqa
#                                                    automobile, gasoline, insurance, mortgage):  # noqa
#     categories = [automobile, gasoline, insurance, mortgage]
#     categories_by_id = {
#         c['id']: c for c in categories
#     }

#     def category_name(category_id):
#         category = categories_by_id[category_id]
#         if category['parent_id'] is None:
#             return category['name']
#         parent_category = categories_by_id[category['parent_id']]
#         return '{}::{}'.format(parent_category['name'], category['name'])

#     for _ in xrange(10):
#         create(account=tangerine_credit_card_account['id'],
#                date=fake.date_time_between_dates(
#                    datetime_start=datetime.datetime(2017, 1, 1),
#                    datetime_end=datetime.datetime(2017, 2, 28)).date(),
#                category_id=random.choice(categories)['id'],
#                )
#     response = requests.get('http://localhost:7000/api/accounts/_all?orderBy=category:asc')
#     assert response.status_code == 200
#     response_json = response.json()
#     category_names = [category_name(r['category_id']) for r in response_json['transactions']]
#     assert category_names == sorted(map(category_name, categories))
