from flask import render_template, redirect, session, jsonify, url_for
from flask_login import login_required

from app.constants import GOOGLE_OAUTH_URL, AccessLevel, SectionType
from app.models import db, User, Section, Attendance
from app.utils import generate_rrule
from app import app

import requests
from dateutil import parser as dp

@app.route('/')
def index():
    """ The splash page. """
    return render_template("index.html")

@app.route('/account-info')
@login_required
def account_info():
    token = session.get('google_token')[0]
    try:
        headers = {'Authorization' : "OAuth {0}".format(token)}
        req = requests.get(GOOGLE_OAUTH_URL, headers=headers)
        response = req.json()
        user = User.lookup_by_google(response['id'])
        return jsonify(req.json())
    except requests.exceptions.RequestException:
        return "YOU FUCKED UP A-A-RON"

@app.route('/test')
@login_required
def test():
    return "Done!"
