from flask import redirect, url_for, Blueprint, request, render_template
from flask_login import login_required, current_user

from app import app
from app.models import Announcement
from app.constants import AccessLevel

import logging
import functools

logger = logging.getLogger(__name__)

assistant = Blueprint('assistant', __name__)


# --------------------------- HELPER FUNCTIONS ---------------------------


def assistant_required(f):
    """ A decorator that ensures the current user is a lab assistant. Otherwise,
    redirects to index.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.access == AccessLevel.ASSISTANT:
            return f(*args, **kwargs)
        logger.info("Staff {0} tried to access lab assistant API".format(current_user.id))
        return redirect(url_for('index', _external=True))
    return login_required(wrapper)


# --------------------------- ROUTES ---------------------------


@assistant.route('/')
@assistant_required
def index():
    """ Root assistant view which holds all the announcements. """
    results = Announcement.all_announcements()
    results = sorted(results, key=lambda x : x['date'], reverse=True)
    return render_template("assistant/index.html", announcements=results)

@assistant.route('/check-in')
@assistant_required
def check_in():
    """ Check in view for lab assistants. """
    print(current_user.access)
    return render_template("assistant/check_in.html")
