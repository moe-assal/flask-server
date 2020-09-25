from flask import Blueprint, request, abort
from white_party import csrf_token, db
from hashlib import sha256
from white_party.modules import ServerState
import os

tasks = Blueprint('tasks', __name__)
SECRET_KEY = os.getenv('SECRET_KEY')
sk_hash = sha256(SECRET_KEY.encode('utf-8')).hexdigest()


@tasks.route('/increment-week-duel', methods=['POST'])
@csrf_token.exempt
def increment_week_duel():
    """
    JSON data needed:
        - password: hash of SECRET_KEY environmental variable.
        - week_duel: this variable is used to make sure sender is not out-of-sync
    """
    data = request.get_json()
    try:
        password = data['password']
        week_duel = data['week-duel']
    except KeyError:
        return abort(404)

    if password == sk_hash and week_duel == ServerState.get_state()['week-duel']:
        print('\n++ incrementing week duel ++\n')
        ServerState.increment_week_duel()
        db.session.commit()
        return ""
    else:
        return abort(404)


@tasks.route('/get-data', methods=['POST'])
@csrf_token.exempt
def get_data():
    """
    JSON data needed:
        - password: hash of SECRET_KEY environmental variable.
        - encoding: the way `datetime` object must be encoded to a string.
    """
    data = request.get_json()
    try:
        encoding = data['encoding']
        password = data['password']
    except KeyError:
        return abort(403)

    state = ServerState.get_state()
    if password == sk_hash:
        return state['launch-date'].strftime(encoding) + '\r' + \
               str(state['week-duel']) + '\r' + str(state['base-date'].strftime(encoding))

    else:
        return abort(302)
