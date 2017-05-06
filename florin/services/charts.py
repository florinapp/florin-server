import copy
import datetime
from decimal import Decimal
from .params import get_date_range_params
from florin.db import Account, Transaction
from sqlalchemy import func, not_


def retrofit(account_histories):
    # Input:
    # {'account': {},
    #  'history': [{'date': ..., 'balance': ...}, {'date': ..., 'balance': ...}]
    # Output:
    #  All accounts have history data points on all dates included in the
    #  response
    account_histories = copy.deepcopy(account_histories)
    accounts = {
        account_history['account']['id']: account_history['account']
        for account_history in account_histories
    }
    all_date_points = sorted(list(set([
        history['date']
        for account_history in account_histories
        for history in account_history['history']
    ])))

    account_balance_by_date = {
        date: {}
        for date in all_date_points
    }

    for account_history in account_histories:
        account = account_history['account']
        data_points = account_history['history']
        i = 0  # i is the index for account_history['history']
        j = 0  # j is the index for all_date_points
        # while i < len(data_points) and j < len(all_date_points):
        while j < len(all_date_points):
            data_point = data_points[i]
            date_point = all_date_points[j]

            if data_point['date'] == date_point:
                # date point exists in the series
                i = min(i + 1, len(data_points) - 1)
                j += 1
                account_balance_by_date[date_point][account['id']] = data_point
            elif data_point['date'] >= date_point:
                j += 1
                balance = Decimal('0') if i == 0 else data_points[i-1]['balance']
                account_balance_by_date[date_point][account['id']] = {'date': date_point,
                                                                      'balance': balance}
            else:
                j += 1
                balance = data_points[i]['balance']
                account_balance_by_date[date_point][account['id']] = {'date': date_point,
                                                                      'balance': balance}

    retval = []

    def find_account_history_by_id(account_id):
        for account_history in retval:
            if account_history.get('account')['id'] == account_id:
                return account_history
        return None

    for date, data_points in sorted(account_balance_by_date.items()):
        for account_id, data_point in data_points.items():
            account_history = find_account_history_by_id(account_id)
            if account_history:
                account_history['history'].append(data_point)
            else:
                account_history = {'account': accounts[account_id],
                                   'history': [data_point]}
                retval.append(account_history)

    return retval


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

    retrofit(response)
    return {'chartData': response}
