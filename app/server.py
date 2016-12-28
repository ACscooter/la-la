from flask import render_template, redirect, session, jsonify, url_for

from .constants import GOOGLE_OAUTH_URL, AccessLevel
from .models import db, User
from app import app

import requests

@app.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for("auth.index"))
    try:
        headers = {'Authorization' : "OAuth {0}".format(access_token)}
        req = requests.get(GOOGLE_OAUTH_URL, headers=headers)
        response = req.json()
        print(response)
        user = User.lookup(response['id'])
        if not user:
            print("Creating new user!")
            user = User(sid=26862806,
                gid=response['id'],
                name=response['name'],
                email=response['email'],
                privilege=AccessLevel.STAFF
            )
            db.session.add(user)
            db.session.commit()
        print(user)
        return jsonify(req.json())
    except requests.exceptions.RequestException:
        # TODO Log this thing
        return "YOU FUCKED UP A-A-RON"

@app.route('/dbtest')
def test():
    if db.session.query("1").from_statement("SELECT 1").all():
        return "YOU DID IT!"
    return "YOU SUCK A LOT!"
