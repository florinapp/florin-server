import pytest
from florin import db
from ..utils import db_fixture


@pytest.fixture
@db_fixture(db.Account)
def td_chequing_account():
    return dict(id=1, institution='TD', name='Chequing', type='Chequing')


@pytest.fixture
@db_fixture(db.Account)
def cibc_savings_account():
    return dict(id=2, institution='CIBC', name='Primary Savings', type='Savings')


@pytest.fixture
@db_fixture(db.Account)
def bmo_chequing_account():
    return dict(id=3, institution='BMO', name='Chequing (USD)', type='Chequing')


@pytest.fixture
@db_fixture(db.Account)
def tangerine_credit_card_account():
    return dict(id=4, institution='Tangerine', name='MasterCard', type='CreditCard')


@pytest.fixture
@db_fixture(db.Account)
def rogers_bank_credit_card_account():
    return dict(id=5, institution='Rogers Bank', name='MasterCard', type='CreditCard')
