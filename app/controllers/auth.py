from flask import redirect, url_for, session, jsonify, Blueprint, request
from flask_oauthlib.client import OAuth, OAuthException
from flask_login import (LoginManager, login_user, logout_user, login_required,
                        current_user)

from app.constants import GOOGLE_REDIRECT_URI, GOOGLE_OAUTH_URL, AccessLevel
from app.models import User, db
from app import app, login_manager

import requests
import json

auth = Blueprint('auth', __name__)


# --------------------------- OAUTH SETUP ---------------------------


oauth = OAuth(app)
google_auth = oauth.remote_app('google',
    consumer_key=app.config['GOOGLE_CLIENT_ID'],
    consumer_secret=app.config['GOOGLE_CLIENT_SECRET'],
    request_token_params={
        'scope' : "email"
    },
    base_url='https://www.googleapis.com/oauth2/v3/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

@google_auth.tokengetter
def get_access_token():
    return session.get('google_token')


# --------------------------- HELPER FUNCTIONS ---------------------------


def user_from_google_token(token):
    """ Returns the user associated with the given Google Sign-in TOKEN. If the
    user does not exist, then creates a new user.
    """
    if not token:
        # LOG THAT SHIT
        return None
    user_data = google_user_data(token)
    if user_data is None:
        # LOG THAT SHIT
        return None
    return user_from_google_id(user_data)


def user_from_google_id(user_data):
    """ Returns the user associated with the USER_DATA. If no such user exists,
    then create the user.

    TODO:   If the user does not exist, then redirect the user to a page to
            confirm information.
    """
    user = User.lookup_by_google(user_data['id'])
    if user is None:
        # LOG THAT SHIT creating new user
        user = User(sid=-1,
            gid=user_data['id'],
            name=user_data['name'],
            email=user_data['email'],
            access=AccessLevel.ASSISTANT
        )
        db.session.add(user)
        db.session.commit()
    return user


def google_user_data(token, timeout=5):
    """ Returns the account information associated with the token. """
    if not token:
        # TODO log that shit
        return None
    try:
        h = {'Authorization' : "OAuth {0}".format(token)}
        request = requests.get(GOOGLE_OAUTH_URL, headers=h, timeout=timeout)
        data = request.json()
        if 'error' not in data and data.get('email'):
            return data
    except requests.exceptions.Timeout as e:
        # TODO loggggggging
        return None


def authorize_user(user):
    if user is None:
        # TODO LOG THAT SHIT
        raise TypeError("Cannot authorize as None")
    login_user(user)
    redirect_to = session.pop('redirect_after_login', None)
    # TODO redirect people based on access level
    return redirect(redirect_to or url_for('index'))

@login_manager.unauthorized_handler
def unauthorized():
    session['redirect_after_login'] = request.url
    return redirect(url_for('auth.index'))

@login_manager.user_loader
def load_user(user_id):
    return User.lookup_by_id(user_id)


# --------------------------- ROUTES ---------------------------


@auth.route('/')
def index():
    token = session.get('google_token')
    if token is None:
        return google_auth.authorize(callback=url_for('auth.authorized', _external=True))
    return redirect(url_for('index'))

@auth.route(GOOGLE_REDIRECT_URI)
def authorized():
    response = google_auth.authorized_response()
    if response is None:
        return "Access denied: reason={0} error={1}".format(
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(response, OAuthException):
        return "{0} - {1}".format(
            resp.data.get('error', 'Unknown Error'),
            resp.data.get('error_description', 'Unknown')
        )

    token = response['access_token']
    user = user_from_google_token(token)
    if not user:
        # Could not log user in.
        # TODO Log this shit
        return redirect(url_for('index'))
    session['google_token'] = (token, '')
    return authorize_user(user)

@auth.route("/logout/", methods=['POST'])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))
