import datetime


def get_date_range_params(args):
    start_date = args.get('startDate', '1970-01-01')
    end_date = args.get('endDate', '9999-12-31')

    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    return start_date, end_date
