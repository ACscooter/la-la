from flask import redirect, url_for, Blueprint, request, render_template
from flask_login import login_required

from app import app
from app.models import Announcement

import logging

logger = logging.getLogger(__name__)

assistant = Blueprint('assistant', __name__)


# --------------------------- HELPER FUNCTIONS ---------------------------


# if you need it


# --------------------------- ROUTES ---------------------------


@assistant.route('/')
@login_required
def index():
    """ Root assistant view which holds all the announcements. """
    results = Announcement.all_announcements()
    return render_template("assistant/index.html", announcements=results)
