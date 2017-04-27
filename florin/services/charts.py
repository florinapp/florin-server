from florin.db import Account
from sqlalchemy import not_


def get_account_balance_chart_data(app, args):
    accounts = (
        Account.query()
        .filter(not_(Account.deleted))
    ).all()

    response = [
        {
            'account': account.to_dict(),
            'history': account.balances
        }
        for account in accounts
    ]
    return {'chartData': response}
