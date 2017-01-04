from flask import redirect, url_for, Blueprint, request, render_template
from flask_login import login_required, current_user

from app import app
from app.models import Announcement
from app.constants import AccessLevel, SEMESTER_START, SEMESTER_LENGTH
from app.utils import get_week_ranges

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
    """ Check in view for lab assistants.

    TODO:   Make this run in time linear w.r.t. the number attendances.
            Currently runs in time num_attendances * len(ranges)
    """
    attendance = current_user.get_all_attendances()
    response = []
    for start, end in get_week_ranges(SEMESTER_START, SEMESTER_LENGTH):
        entry = []
        in_range = [row for row in attendance if row.section_date >= start and row.section_date <= end]
        for row in in_range:
            entry.append({
                'date' : row.section_date,
                'type' : row.section.section_type,
                'instructor_name' : row.section.instructor.name,
                'location' : row.section.location,
                'section_id' : row.section_id
            })
        entry = sorted(entry, key=lambda x : x['date'], reverse=True)
        response.append(entry)
    response.reverse()
    return render_template("assistant/check_in.html", attendance=response)
