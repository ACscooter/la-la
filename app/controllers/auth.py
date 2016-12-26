from flask import redirect, url_for, session, jsonify, Blueprint
from flask_oauth import OAuth

from auth import auth

import requests
import json

GOOGLE_REDIRECT_URI = "/oauth2callback"
GOOGLE_OAUTH_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

auth = Blueprint('auth', __name__)

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


# Take a url to redirect back to and then start a user session?
@auth.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('authorized', _external=True)
        return google.authorize(callback=callback)
    return redirect(url_for('index'))
    # access_token = access_token[0]

    # try:
    #     headers = {'Authorization' : "OAuth {0}".format(access_token)}
    #     req = requests.get(GOOGLE_OAUTH_URL, headers=headers)
    #     return jsonify(req.json())
    # except requests.exceptions.RequestException:
    #     # TODO Log this thing
    #     return "YOU FUCKED UP A-A-RON"

@auth.route(GOOGLE_REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('auth.index'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')
