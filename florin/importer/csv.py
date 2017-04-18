from __future__ import absolute_import
import csv
import calendar
import json
import decimal
import datetime


class CSVImporter(object):
    def _import(self, file_storage, transaction_class):
        result = []
        reader = csv.DictReader(file_storage)
        for line in reader:
            attrs = {}
            for key, (csv_key, transform_fn) in transaction_class.MAPPING.items():
                if isinstance(csv_key, str):
                    csv_keys = [csv_key]
                else:
                    csv_keys = csv_key

                for csv_key in csv_keys:
                    if csv_key in line:
                        break

                attrs[key] = transform_fn(line[csv_key])
            result.append(transaction_class(**attrs))
        return result

    def import_from(self, file_storage):
        result = None
        for _, transaction_class in TRANSACTION_CLASS.items():
            try:
                file_storage.seek(0)
                result = self._import(file_storage, transaction_class)
            except Exception:
                continue
        return result, None  # csv importer doesn't deal with account balances


def _parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%m/%d/%Y')


def _parse_amount(amount_str):
    return decimal.Decimal(amount_str.replace('$', '').replace(',', '').replace('(', '').replace(')', ''))


def default(obj):
    """Default JSON serializer."""

    if isinstance(obj, datetime.datetime):
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis


class TangerineTransaction(dict):
    transaction_date = None
    transaction_type = None
    name = None
    memo = None
    amount = None

    HASH_FIELDS = [
        'transaction_date',
        'transaction_type',
        'name',
        'memo',
        'amount',
    ]

    MAPPING = dict(
        transaction_date=(['Transaction date', 'Date'], _parse_date),
        transaction_type=('Transaction', str.lower),
        name=('Name', str),
        memo=('Memo', str),
        amount=('Amount', _parse_amount),
    )

    def __init__(self, *args, **kwargs):
        super(TangerineTransaction, self).__init__(*args, **kwargs)

    @property
    def common_attrs(self):
        return dict(
            date=self['transaction_date'],
            info=self['memo'],
            payee=self['name'],
            memo=json.dumps(self, default=default),
            amount=self['amount'],
            transaction_type='credit' if self['amount'] > 0 else 'debit',
        )


class RogersTransaction(dict):
    transaction_date = None
    posting_date = None
    amount = None
    merchant = None
    merchant_city = None
    merchant_province = None
    merchant_postalcode = None
    reference_number = None
    sic_mcc = None
    is_internal_transfer = None

    MAPPING = dict(
        transaction_date=('Transaction Date', _parse_date),
        posting_date=(' Posting Date', _parse_date),
        amount=(' Billing Amount', _parse_amount),
        merchant=(' Merchant', str),
        merchant_city=(' Merchant City ', str),
        merchant_province=(' Merchant Province/State ', str),
        merchant_postalcode=(' Merchant Postal Code/Zip ', str),
        reference_number=(' Reference Number ', str),
        debit_or_credit=(' Debit/Credit Flag ', str),
        sic_mcc=(' SIC/MCC Code', str),
    )

    def __init__(self, *args, **kwargs):
        super(RogersTransaction, self).__init__(*args, **kwargs)

    @property
    def common_attrs(self):
        transaction_type = 'credit' if self['debit_or_credit'].lower() == 'c' else 'debit'
        return dict(
            date=self['transaction_date'],
            info=' '.join([self['merchant'], self['merchant_city'],
                           self['merchant_province'], self['merchant_postalcode']]),
            payee=self['merchant'],
            memo=json.dumps(self, default=default),
            amount=self['amount'] if transaction_type == 'credit' else -1 * self['amount'],
            transaction_type=transaction_type,
        )


TRANSACTION_CLASS = {
    'TangerineTransaction': TangerineTransaction,
    'RogersTransaction': RogersTransaction,
}
