import os
import functools
import flask
import logging
import datetime
from decimal import Decimal
from flask_cors import CORS
from flask.json import JSONEncoder
from . import db
from .services import transactions, exceptions, accounts, categories


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

        return super(MyJSONEncoder, self).default(obj)


def create_app():
    app = flask.Flask(__name__)
    app.json_encoder = MyJSONEncoder
    CORS(app)
    db.init(app, os.getenv('DBFILE'))
    return app


app = create_app()


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


@app.route('/api/categories', methods=['GET'])
@jsonify()
@handle_exceptions
def get_categories():
    return categories.get(app)


@app.route('/api/accounts/<account_id>/upload', methods=['POST'])
@jsonify()
@handle_exceptions
def upload_transactions(account_id):
    return accounts.upload(app, account_id, flask.request.files)


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
