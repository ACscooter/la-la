from flask import redirect, url_for, session, jsonify, Blueprint
from flask_oauth import OAuth

from ..constants import GOOGLE_REDIRECT_URI
from app import app, login_manager

import requests
import json

auth = Blueprint('auth', __name__)




# --------------------------- OAUTH SETUP ---------------------------


oauth = OAuth()
google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={
        'scope' : 'https://www.googleapis.com/auth/userinfo.email',
        'response_type': 'code'
    },
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=app.config['GOOGLE_CLIENT_ID'],
    consumer_secret=app.config['GOOGLE_CLIENT_SECRET']
)

@google.tokengetter
def get_access_token():
    return session.get('access_token')


# --------------------------- HELPER FUNCTIONS ---------------------------




@auth.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('auth.authorized', _external=True)
        return google.authorize(callback=callback)
    return redirect(url_for('index'))

@auth.route(GOOGLE_REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('auth.index'))
