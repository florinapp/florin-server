import datetime
from .params import get_date_range_params
from florin.db import Account, Transaction
from sqlalchemy import func, not_


def get_account_balance_chart_data(app, args):
    start_date, end_date = get_date_range_params(args)

    accounts = (
        Account.query()
        .filter(not_(Account.deleted))
    ).all()

    response = []

    for account in accounts:
        account_history = {'account': account.to_dict(),
                           'history': []}
        balances_in_date_range = [
            balance for balance in account.balances
            if start_date <= balance.date <= end_date
        ]

        if not balances_in_date_range:
            continue

        latest_balance = balances_in_date_range[-1]

        if len(balances_in_date_range) == 1:
            account_history['history'].append({
                'date': latest_balance.date,
                'balance': latest_balance.balance
            })
        if len(balances_in_date_range) > 1:
            account_history['history'].append({
                'date': latest_balance.date,
                'balance': latest_balance.balance
            })
            account_history['history'].append({
                'date': balances_in_date_range[0].date,
                'balance': balances_in_date_range[0].balance
            })

        delta_by_date = (
            app.session.query(Transaction.date, func.sum(Transaction.amount))
            .filter(Transaction.account_id == account.id)
            .filter(not_(Transaction.deleted))
            .filter(Transaction.date <= min(latest_balance.date, end_date))
            .filter(Transaction.date >= start_date)
            .order_by(Transaction.date.desc())
            .group_by(Transaction.date)
        ).all()

        next_balance = latest_balance.balance
        for date, delta_amount in delta_by_date:
            balance = next_balance - delta_amount
            account_history['history'].append({
                'date': date + datetime.timedelta(days=-1),
                'balance': balance
            })
        account_history['history'].sort(key=lambda h: h['date'])
        response.append(account_history)

    return {'chartData': response}
