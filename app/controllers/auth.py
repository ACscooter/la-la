from flask import redirect, url_for, session, jsonify, Blueprint, request
from flask_oauthlib.client import OAuth, OAuthException
from flask_login import (LoginManager, login_user, logout_user, login_required,
                        current_user)

from app.constants import GOOGLE_OAUTH_URL, AccessLevel
from app.models import User, db
from app import app, login_manager

import requests
import logging
import json

logger = logging.getLogger(__name__)

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
        logger.info("CALLING(user_from_google_token) : user token is NONE")
        return None
    user_data = google_user_data(token)
    if user_data is None:
        logger.info("CALLING(user_from_google_token) : user data is NONE")
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
        logger.info("CALLING(user_from_google_id) Creating user email={}".format(
            user_data['email'])
        )
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
        logger.info("CALLING(google_user_data) user token is NONE")
        return None
    try:
        h = {'Authorization' : "OAuth {0}".format(token)}
        request = requests.get(GOOGLE_OAUTH_URL, headers=h, timeout=timeout)
        data = request.json()
        if 'error' not in data and data.get('email'):
            return data
    except requests.exceptions.Timeout as e:
        logger.warning("CALLING(google_user_data) user data request timeout")
        return None


def authorize_user(user):
    if user is None:
        logger.warning("CALLING(authorize_user) user is NONE")
        raise TypeError("Cannot authorize as None")
    login_user(user)
    redirect_to = session.pop('redirect_after_login', None)
    # TODO redirect people based on access level
    return redirect(redirect_to or url_for('index', _external=True))

@login_manager.unauthorized_handler
def unauthorized():
    session['redirect_after_login'] = request.url
    return redirect(url_for('auth.index', _external=True))

@login_manager.user_loader
def load_user(user_id):
    return User.lookup_by_id(user_id)


# --------------------------- ROUTES ---------------------------


@auth.route('/')
def index():
    """ Logging in begins here. If the user is already authenticated, then
    simply redirect them to another page.

    TODO:   Figure out where to redirect already authenticated users to.
    """
    token = session.get('google_token')
    if token is None:
        callback = url_for('auth.authorized', _external=True)
        print(">> CALLBACK ADDRESS: " + callback)
        return google_auth.authorize(callback=callback)
    # Already signed in
    return redirect(url_for('index', _external=True))

@auth.route('/authorized')
def authorized():
    print(">> CURRENTLY IN CALLBACK!")
    response = google_auth.authorized_response()
    print(response)
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
        logger.warning("CALLING(authorize_user) attempt to get user FAILED")
        return redirect(url_for('index', _external=True))
    session['google_token'] = (token, '')
    return authorize_user(user)

@auth.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index', _external=True))
