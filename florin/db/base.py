import contextlib
import hashlib
import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Float, UnicodeText, DateTime, Text, Boolean, UniqueConstraint)


Base = declarative_base()


class ToDictMixin(object):
    __export__ = []  # subclass must define

    def _get_value(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            return getattr(self, key)

    def to_dict(self, extra_fields=None):
        assert hasattr(self, '__export__')
        total_fields = list(self.__export__)
        total_fields.extend(extra_fields or [])
        return {
            k: self._get_value(k) for k in total_fields
        }


class SearchByIdMixin(object):
    @classmethod
    def get_by_id(cls, id):
        return cls.session.query(cls).filter_by(id=id).one()


class QueryMixin(object):
    @classmethod
    def query(cls):
        return cls.session.query(cls)


class Account(Base, ToDictMixin, SearchByIdMixin, QueryMixin):
    __tablename__ = 'accounts'
    __export__ = ['id', 'institution', 'name', 'type']

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    type = Column(String(32), ForeignKey('account_types.name'), nullable=False)
    signature = Column(String(64), nullable=True)  # TODO: remove
    deleted = Column(Boolean, nullable=False, default=False)
    balances = relationship('AccountBalance', order_by='AccountBalance.date')
    transactions = relationship('Transaction')


class AccountType(Base, ToDictMixin, QueryMixin):
    __tablename__ = 'account_types'
    __export__ = ['name']

    name = Column(String, primary_key=True)


class AccountBalance(Base, ToDictMixin, SearchByIdMixin, QueryMixin):
    __tablename__ = 'account_balances'
    __table_args__ = (UniqueConstraint('account_id', 'date', name='unique_account_id_and_date'),)
    __export__ = ['id', 'account_id', 'date', 'balance']

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    date = Column(Date, nullable=False)
    balance = Column(Float(as_decimal=True), nullable=False)


class Transaction(Base, ToDictMixin, SearchByIdMixin, QueryMixin):
    __tablename__ = 'transactions'
    __export__ = ['id', 'date', 'info', 'payee', 'memo', 'amount', 'transaction_type', 'category_id']

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    info = Column(String(255), nullable=True)
    payee = Column(String(255), nullable=False)
    memo = Column(UnicodeText)
    amount = Column(Float(as_decimal=True), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    transaction_type = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    checksum = Column(String(128), nullable=False, unique=True)
    deleted = Column(Boolean, nullable=False, default=False)

    @staticmethod
    def _calculate_checksum(attrs):
        fields = ['date', 'info', 'payee', 'memo', 'amount', 'transaction_type']
        sig = '&'.join([str(attrs[field]) for field in fields])
        print(sig)
        return 'sha256:{}'.format(hashlib.sha256(sig).hexdigest())

    def __init__(self, *args, **kwargs):
        checksum = kwargs.pop('checksum', None)
        if checksum is None:
            checksum = self._calculate_checksum(kwargs)
        kwargs['checksum'] = checksum
        super(Transaction, self).__init__(*args, **kwargs)


class Category(Base, ToDictMixin, SearchByIdMixin):
    __tablename__ = 'categories'
    __export__ = ['id', 'name', 'parent_id', 'type']

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    type = Column(String(16), nullable=False)
    parent = relationship('Category', remote_side=[id])


class FileUpload(Base, SearchByIdMixin, QueryMixin):
    __tablename__ = 'file_uploads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    file_content = Column(Text, nullable=False)  # base64-encoded
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    account_signature = Column(String(128), nullable=True)


def get_engine(dbfile):
    return sqlalchemy.create_engine('sqlite:///{}'.format(dbfile))


def make_session(engine):
    return sessionmaker(bind=engine)()


def init(app, dbfile):
    engine = get_engine(dbfile)
    session = make_session(engine)
    Base.session = session
    app.session = session


@contextlib.contextmanager
def db_transaction(session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
