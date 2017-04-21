import random
from decimal import Decimal
from florin import db
from ..utils import db_fixture
from faker import Faker


fake = Faker()


def random_amount():
    return Decimal(str(abs(random.gauss(50, 55))))


@db_fixture(db.AccountBalance)
def create(**kwargs):
    return dict(
        account_id=kwargs['account_id'],
        date=kwargs.get('date', fake.date_time_this_month(before_now=True, after_now=False).date()),
        balance=kwargs.get('balance', random_amount())
    )
