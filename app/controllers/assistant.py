from flask import redirect, url_for, Blueprint, request, render_template
from flask_login import login_required

from app import app

import logging

logger = logging.getLogger(__name__)

assistant = Blueprint('assistant', __name__)


# --------------------------- HELPER FUNCTIONS ---------------------------


# if you need it


# --------------------------- ROUTES ---------------------------


@assistant.route('/')
@login_required
def index():
    """ Root assistant view. """
    return render_template("assistant/index.html")
