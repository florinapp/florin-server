import datetime
from florin.db import Account, Transaction
from sqlalchemy import not_, func


def get_account_balance_chart_data(app, args):
    accounts = (
        Account.query()
        .filter(not_(Account.deleted))
    ).all()

    response = []

    for account in accounts:
        account_history = {'account': account.to_dict(),
                           'history': []}
        if len(account.balances) == 0:
            continue

        latest_balance = account.balances[-1]
        account_history['history'].append([latest_balance.date, latest_balance.balance])

        delta_by_date = (
            app.session.query(Transaction.date, func.sum(Transaction.amount))
            .join(Account)
            .filter(Transaction.account_id == account.id)
            .filter(not_(Transaction.deleted))
            .filter(Transaction.date <= latest_balance.date)
            .order_by(Transaction.date.desc())
            .group_by(Transaction.date)
        ).all()

        next_balance = latest_balance.balance
        for date, delta_amount in delta_by_date:
            balance = next_balance - delta_amount
            account_history['history'].append([date + datetime.timedelta(days=-1), balance])
        account_history['history'] = list(reversed(account_history['history']))
        response.append(account_history)

    return {'chartData': response}
