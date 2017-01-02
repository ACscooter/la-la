from flask import render_template, redirect, session, jsonify, url_for
from flask_login import login_required

from app.constants import GOOGLE_OAUTH_URL, AccessLevel, SectionType
from app.models import db, User, Section, Attendance, Announcement
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
        print(user.id)
        Announcement.make_announcement(user, "Balloons in Soda Courtyard", "Hey everyone, there are balloons in the soda courtyard right now. Like shit I'm tripping balls.", tags="balloons, fun time, soda hall, cs for lyfe")
        Announcement.make_announcement(user, "Hilfinger is in the Soda", "I repeat, the hilf is back.", tags="hilfinger, too, op")
        Announcement.make_announcement(user, "Classes canceled", "CS61A is canceled forever. BUT CS61B IS ALWAYS ON BABY", tags="what, testing, why tho")

        return jsonify(req.json())
    except requests.exceptions.RequestException:
        return "YOU FUCKED UP A-A-RON"

@app.route('/test')
@login_required
def test():
    return "Done!"
