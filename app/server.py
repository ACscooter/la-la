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
    person_a = User.lookup_by_sid(1337)
    enrollments = person_a.get_sections_enrolled()
    for entry in enrollments:
        print("Enrolled in " + entry.section_id)
    new_section = Section(section_id="ABC123",
        section_type=SectionType.LAB,
        instructor_id=9,
        date_rule=generate_rrule("01/06/1997", "09:00:00"),
        location="Soda Hall 310"
    )
    # new_section.add_section()
    person_a.enroll("ABC123")
    date = dp.parse("01/13/1997")
    person_a.mark_present("ABC123", date)
    ta = User.lookup_by_sid(26862806)
    attend = Attendance.lookup_by_assistant_section_date(person_a.id, 8, date)
    attend.confirm_attendance(ta)
    return "Done!"
