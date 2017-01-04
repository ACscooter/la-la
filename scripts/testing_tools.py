from app.models import (User, Section, Enrollment, Attendance, Announcement,
                        disposable_session)
from app.constants import SectionType, AttendanceType, AccessLevel, SEMESTER_START, SEMESTER_LENGTH
from app.utils import generate_rrule

import dateutil.rrule as dr
import dateutil.parser as dp


SECTION_LOCATION = "Soda Hall Room 310"

def create_test_section(instructor_id, section_id, start_date=SEMESTER_START, num_weeks=SEMESTER_LENGTH):
    """ Creates a test section at START_DATE for NUM_WEEKS. """
    session = disposable_session()
    rule = dr.rrule(dr.WEEKLY, dtstart=start_date, count=num_weeks)
    new_section = Section(section_id=section_id,
        section_type=SectionType.LAB,
        instructor_id=instructor_id,
        date_rule=rule,
        location=SECTION_LOCATION
    )
    session.add(new_section)
    session.commit()
    session.close()

def create_test_enrollment(user_id, section_id):
    """ Enrolls USER_ID to SECTION_ID. """
    session = disposable_session()
    new_enrollment = Enrollment(user_id=user_id, section_id=section_id)
    session.add(new_enrollment)
    session.commit()
    session.close()

def create_test_attendance(section_date):
    """ Marks all sections on SECTION_DATE as unmarked. """
    section_date = dp.parse(section_date)
    session = disposable_session()
    all_assistants = session.query(User).filter_by(access=AccessLevel.ASSISTANT).all()
    for assistant in all_assistants:
        # print(assistant.id, assistant.name)
        enrolled = [row.section_id for row in session.query(Enrollment).filter_by(user_id=assistant.id)]
        sections = [session.query(Section).filter_by(id=sect_id).one_or_none() for sect_id in enrolled]
        for section in sections:
            # print(assistant.id, assistant.name, section.id, section.section_id)
            new_attendance = Attendance(assistant_id=assistant.id,
                section_id=section.id,
                section_date=section_date,
                attendance_type=AttendanceType.UNMARKED
            )
            session.add(new_attendance)
    session.commit()
    session.close()
