import hashlib
import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, UnicodeText, DateTime, Text, Boolean


Base = declarative_base()


class ToDictMixin(object):
    __export__ = []  # subclass must define

    def to_dict(self):
        assert hasattr(self, '__export__')
        return {
            k: self.__dict__[k] for k in self.__export__
        }


class SearchByIdMixin(object):
    @classmethod
    def get_by_id(cls, id):
        return cls.session.query(cls).filter_by(id=id).one()


class Account(Base, ToDictMixin, SearchByIdMixin):
    __tablename__ = 'accounts'
    __export__ = ['id', 'institution', 'name', 'type']

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    signature = Column(String(64), nullable=True)  # TODO: remove
    deleted = Column(Boolean, nullable=False, default=False)
    balances = relationship('AccountBalance')


class AccountBalance(Base, ToDictMixin):
    __tablename__ = 'account_balances'
    __export__ = ['id', 'account_id', 'date', 'balance']

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    date = Column(Date, nullable=False)
    balance = Column(Float(as_decimal=True), nullable=False)


class Transaction(Base, ToDictMixin, SearchByIdMixin):
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


class FileUpload(Base, SearchByIdMixin):
    __tablename__ = 'file_uploads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    file_content = Column(Text, nullable=False)  # base64-encoded
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    account_signature = Column(String(128), nullable=True)


def get_engine(dbfile):
    return sqlalchemy.create_engine('sqlite:///{}'.format(dbfile))


def init(app, dbfile):
    engine = get_engine(dbfile)
    session = sessionmaker(bind=engine)()
    Base.session = session
    app.session = session
