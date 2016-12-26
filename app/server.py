from flask import render_template, redirect, session, jsonify, url_for

from .constants import GOOGLE_OAUTH_URL
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
        return jsonify(req.json())
    except requests.exceptions.RequestException:
        # TODO Log this thing
        return "YOU FUCKED UP A-A-RON"
