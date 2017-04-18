import uuid
import random
from decimal import Decimal
from florin import db
from florin.services.categories import TBD_CATEGORY_ID
from ..utils import db_fixture
from faker import Faker


fake = Faker()


def random_amount():
    return Decimal(str(abs(random.gauss(50, 55))))


@db_fixture(db.Transaction)
def create(**kwargs):
    attrs = dict(
        date=kwargs.get('date', fake.date_time_this_month(before_now=True, after_now=False).date()),
        payee=kwargs.get('payee', fake.company()),
        memo=kwargs.get('memo', fake.text(max_nb_chars=20)),
        amount=kwargs.get('amount', random_amount()),
        category_id=kwargs.get('category_id', TBD_CATEGORY_ID),
        account_id=kwargs['account_id'],
        transaction_type=kwargs.get('transaction_type', random.choice(['expense', 'income'])),
        checksum=kwargs.get('checksum', uuid.uuid4().hex)
    )
    if attrs['transaction_type'] == 'expense' and attrs['amount'] > 0:
        attrs['amount'] = -1 * attrs['amount']
    return attrs
