import os
import functools
import flask
import logging
import datetime
from decimal import Decimal
from flask_cors import CORS
from flask.json import JSONEncoder
from . import db
from .services import charts, transactions, exceptions, accounts, categories, uploads


logging.basicConfig(level='DEBUG')


def handle_exceptions(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except exceptions.ResourceNotFound:
            flask.abort(404)
        except exceptions.InvalidRequest as e:
            flask.abort(flask.make_response(flask.jsonify({
                'error': str(e)
            }), 400))

    return wrapper


def jsonify(success_status_code=200):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)
            return flask.jsonify(response), success_status_code
        return wrapper
    return decorator


class MyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(round(obj, 2))
        if isinstance(obj, float):
            return str(round(Decimal(str(obj)), 2))
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, db.ToDictMixin):
            return obj.to_dict()

        return super(MyJSONEncoder, self).default(obj)


def create_app():
    app = flask.Flask(__name__)
    app.json_encoder = MyJSONEncoder
    CORS(app)
    db.init(app, os.getenv('DBFILE'))
    return app


app = create_app()


@app.route('/api/fileUploads', methods=['POST'])
@jsonify()
@handle_exceptions
def upload_files():
    return uploads.upload(app, flask.request.files)


@app.route('/api/fileUploads/<file_upload_id>/linkAccount', methods=['POST'])
@jsonify()
@handle_exceptions
def link_file_upload_with_account(file_upload_id):
    return uploads.link(app, file_upload_id, flask.request.json)


@app.route('/api/accounts', methods=['GET'])
@jsonify()
@handle_exceptions
def get_accounts():
    return accounts.get(app)


@app.route('/api/accounts', methods=['POST'])
@jsonify(success_status_code=201)
@handle_exceptions
def post_accounts():
    return accounts.post(app, flask.request.json)


@app.route('/api/accounts/<account_id>', methods=['PUT'])
@jsonify()
@handle_exceptions
def put_accounts(account_id):
    return accounts.put(app, account_id, flask.request.json)


@app.route('/api/accounts/<account_id>', methods=['DELETE'])
@jsonify()
@handle_exceptions
def delete_accounts(account_id):
    return accounts.delete(app, account_id)


@app.route('/api/categories', methods=['GET'])
@jsonify()
@handle_exceptions
def get_categories():
    return categories.get(app)


@app.route('/api/accounts/<account_id>', methods=['GET'])
@jsonify()
@handle_exceptions
def get_transactions(account_id):
    return transactions.get(app, account_id, flask.request.args)


@app.route('/api/accounts/<account_id>/categorySummary', methods=['GET'])
@jsonify()
@handle_exceptions
def get_account_summary(account_id):
    return accounts.get_summary(app, account_id, flask.request.args)


@app.route('/api/transactions/<transaction_id>', methods=['PUT'])
@jsonify()
@handle_exceptions
def update_transaction(transaction_id):
    return transactions.update(app, transaction_id, flask.request.json)


@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
@jsonify()
@handle_exceptions
def delete_transaction(transaction_id):
    return transactions.delete(app, transaction_id)


@app.route('/api/accounts/<account_id>/balances', methods=['GET'])
@jsonify()
@handle_exceptions
def get_account_balances(account_id):
    return accounts.get_balances(app, account_id)


@app.route('/api/accounts/<account_id>/balances', methods=['POST'])
@jsonify()
@handle_exceptions
def post_account_balances(account_id):
    return accounts.post_balances(app, account_id, flask.request.json)


@app.route('/api/accounts/<account_id>/balances/<id>', methods=['DELETE'])
@jsonify()
@handle_exceptions
def delete_account_balances(account_id, id):
    return accounts.delete_balances(app, account_id, id)


@app.route('/api/charts/accountBalances', methods=['GET'])
@jsonify()
@handle_exceptions
def get_account_balance_chart_data():
    return charts.get_account_balance_chart_data(app, flask.request.args)


@app.route('/api/accountTypes', methods=['GET'])
@jsonify()
@handle_exceptions
def get_account_types():
    return accounts.get_types(app)
