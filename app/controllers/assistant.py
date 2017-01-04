from flask import redirect, url_for, Blueprint, request, render_template
from flask_login import login_required, current_user
from dateutil import parser as dp

from app import app
from app.models import Announcement, User
from app.constants import AccessLevel, AttendanceType, SEMESTER_START, SEMESTER_LENGTH, DATE_FORMAT_CHECK_IN, DATE_FORMAT_STANDARD
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


def format_confirmed_string(attendance_entry):
    """ Formats the confirmed date string given a row in the Attendance
    table.
    """
    confirmed = ""
    if attendance_entry.attendance_type != AttendanceType.UNMARKED:
        confirmed = "pending {0}".format(attendance_entry.attendance_type.value)
    if attendance_entry.confirmation_date is not None:
        confirmed = "confirmed on {0}".format(row.confirmation_date.strftime(DATE_FORMAT_STANDARD))
    return confirmed.upper()


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
    TODO:   Only return weeks up to the current date.
    """
    attendance = current_user.get_all_attendances()
    payload = []
    for start, end in get_week_ranges(SEMESTER_START, SEMESTER_LENGTH):
        entry = []
        in_range = [row for row in attendance if row.section_date >= start and row.section_date <= end]
        for row in in_range:
            entry.append({
                'date' : row.section_date,
                'date_format' : row.section_date.strftime(DATE_FORMAT_CHECK_IN),
                'type' : row.section.section_type.value,
                'confirmed' : format_confirmed_string(row),
                'instructor_name' : row.section.instructor.name,
                'location' : row.section.location,
                'section_id' : row.section.section_id,
                'assistant_id' : current_user.id
            })
        entry = sorted(entry, key=lambda x : x['date'], reverse=True)
        payload.append(entry)
    week_count = [(i + 1) for i in range(SEMESTER_LENGTH)]
    payload = list(zip(week_count, payload))
    payload.reverse()
    return render_template("assistant/check_in.html", attendance=payload)

@assistant.route('/check-in/submit', methods=['POST'])
@login_required
def submit_check_in():
    assistant = User.lookup_by_id(request.form['assistant_id'])
    attendance = AttendanceType(request.form['attendance_type'])
    date = dp.parse(request.form['date'])
    # section_id = int()
    assistant.mark_attendance(request.form['section_id'], date, attendance)
    return redirect(url_for("assistant.check_in", _external=True))
