import datetime
import decimal
from florin.services.charts import retrofit


def _acct(id):
    return {'name': 'ACCOUNT{}'.format(id), 'id': id}


def _history_point(date_str, balance):
    return {
        'date': datetime.datetime.strptime(date_str, '%Y-%m-%d'),
        'balance': decimal.Decimal(balance)
    }


def _acct_history(id, history_points):
    return {
        'account': _acct(id),
        'history': history_points,
    }


def test_retrofit___no_data_points_need_retrofitting():
    account_histories = [
        _acct_history(1, [_history_point('2017-01-01', '59.99'),
                          _history_point('2017-02-01', '159.99')]),
        _acct_history(2, [_history_point('2017-01-01', '0'),
                          _history_point('2017-02-01', '1.99')])
    ]
    assert account_histories == retrofit(account_histories)


def test_retrofit___retrofit_account2_middle_point():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-03-01', '1.99'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '0'),
            _history_point('2017-03-01', '1.99'),
        ])
    ]
    assert actual_histories == expected_histories


def test_retrofit___retrofit_account1_middle_point():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-03-01', '159.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '1.99'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '59.99'),
            _history_point('2017-03-01', '159.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '1.99'),
        ])
    ]
    assert actual_histories == expected_histories


def test_retrofit___retrofit_account2_multiple_middle_points():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '100.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-04-01', '1.99'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '100.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '0'),
            _history_point('2017-03-01', '0'),
            _history_point('2017-04-01', '1.99'),
        ])
    ]
    assert actual_histories == expected_histories


def test_retrofit___retrofit_account2_starting_point():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-04-01', '1.99'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '0'),
            _history_point('2017-03-01', '0'),
            _history_point('2017-04-01', '1.99'),
        ])
    ]
    assert actual_histories == expected_histories


def test_retrofit___retrofit_account1_starting_point():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '100'),
            _history_point('2017-02-01', '200'),
            _history_point('2017-03-01', '300'),
            _history_point('2017-04-01', '400'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '0'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '100'),
            _history_point('2017-02-01', '200'),
            _history_point('2017-03-01', '300'),
            _history_point('2017-04-01', '400'),
        ])
    ]
    assert actual_histories == expected_histories


def test_retrofit___retrofit_account2_ending_point():
    account_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '1.99'),
        ]),
    ]
    actual_histories = retrofit(account_histories)
    expected_histories = [
        _acct_history(1, [
            _history_point('2017-01-01', '59.99'),
            _history_point('2017-02-01', '159.99'),
            _history_point('2017-03-01', '159.99'),
            _history_point('2017-04-01', '1.99'),
        ]),
        _acct_history(2, [
            _history_point('2017-01-01', '1.99'),
            _history_point('2017-02-01', '1.99'),
            _history_point('2017-03-01', '1.99'),
            _history_point('2017-04-01', '1.99'),
        ])
    ]
    assert actual_histories == expected_histories
