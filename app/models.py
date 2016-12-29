from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import MetaData, Column, ForeignKey, types
from sqlalchemy.dialects import mysql

from app.constants import AccessLevel, SectionType, AttendanceType
from app.utils import check_sections_csv, generate_rrule, date_in_rule

import functools
import logging
import pickle
import json

logger = logging.getLogger(__name__)

convention = {
    'ix' : "ix_%(column_0_label)s",
    'uq' : "uq_%(table_name)s_%(column_0_name)s",
    'fk' : "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    'pk' : "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)


# --------------------------- HELPERS ---------------------------


def transaction(f):
    """ Decorator for database (session) transactions."""
    @functools.wraps(f)
    def wrapper(*args, **kwds):
        try:
            value = f(*args, **kwds)
            db.session.commit()
            return value
        except Exception as e:
            logger.warning("Could not write to the DB: {}".format(e))
            db.session.rollback()
            raise
    return wrapper


class TimeRule(types.TypeDecorator):
    """ Custom type for Dateutil rrule object. Simply pickles the object and
    stores it as Text
    """

    impl = types.Text

    def process_bind_param(self, value, dialect):
        # Python -> SQL
        return pickle.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        # SQL -> Python
        return pickle.loads(value)  if value is not None else None



# --------------------------- MODELS ---------------------------


class User(db.Model, UserMixin):
    """ A model for Users. """

    __tablename__ = "users"
    id = Column(db.Integer, primary_key=True)
    sid = Column(db.Integer, unique=True)
    gid = Column(db.Integer, nullable=False, unique=True)
    name = Column(db.String(255))
    email = Column(db.String(255), nullable=False)
    access = Column(types.Enum(AccessLevel), nullable=False)

    # Relationships
    sections = db.relationship("Section")
    enrolled = db.relationship("Enrollment")
    attended = db.relationship("Attendance")

    def get_sections_instructed(self):
        """ Returns all sections the user is teaching. """
        if self.access == AccessLevel.STAFF or self.access == AccessLevel.ADMIN:
            return self.sections
        return []

    def get_sections_enrolled(self):
        """ Returns all sections the user is enrolled in. """
        if self.access == AccessLevel.ASSISTANT:
            return self.enrolled
        return []

    def get_all_attendances(self):
        """ Returns all attendance entries for user. """
        if self.access == AccessLevel.ASSISTANT:
            return self.attended
        return []

    def mark_present(section_id, date):
        """ Marks the student as present from SECTION_ID on DATE. """
        mark_attendance(section_id, date, AttendanceType.PRESENT)

    def mark_absent(section_id, date):
        """ Marks the student as absent from SECTION_ID on DATE. """
        mark_attendance(section_id, date, AttendanceType.ABSENT)

    @transaction
    def mark_attendance(section_id, date, attend):
        """ Marks the student as ATTEND from SECTION_ID on DATE. If element
        with SECTION_ID and DATE already exists, then updates the attendance
        to ATTEND.
        """
        if self.access != AccessLevel.ASSISTANT:
            logger.info("Set attendance error for {0}: staff member".format(self.name))
            raise TypeError("Cannot set attendance for staff")
        section = Section.lookup_by_section_id(section_id)
        if not section.is_valid_date(date):
            logger.info("Set attendance error for {0}: wrong date {1}".format(
                self.name,
                date
            ))
            raise TypeError("Cannot set attendance for section on {0}".format(date))
        attend = Attendance.lookup_by_assistant_section_date(self.id, section_id, date)
        if attend is None:
            attend = Attendance(date=date,
                user_id=user.id,
                section_id=section.id,
                attendance_type=attend
            )
            db.session.add(attend)
        else:
            attend.attendance_type = attend

    @transaction
    def enroll(self, section_id):
        """ Enrolls an assistant in a section. """
        section = Section.lookup_by_section_id(section_id)
        if self.access != AccessLevel.ASSISTANT:
            logger.info("Enrolling {0} to {1} error: cannot enroll staff member".format(
                self.name,
                section_id
            ))
            raise TypeError("Cannot enroll staff member")
        if section is None:
            logger.info("Enrolling {0} to {1} error: section does not exist".format(
                self.name,
                section_id
            ))
            raise TypeError("Section does not exist")
        enrollment = Enrollment.lookup_by_assistant_section(user_id, section_id)
        if enrollment is None:
            enrollment = Enrollment(user_id=self.id, section_id=section.id)
            db.session.add(enrollment)

    @staticmethod
    def lookup_by_google(google_id):
        """ Gets a user with the google assigned user id. """
        return User.query.filter_by(gid=google_id).one_or_none()

    @staticmethod
    def lookup_by_id(user_id):
        """ Gets the User id by the primary key. """
        return User.query.get(user_id)

    @staticmethod
    def lookup_by_sid(student_id):
        """ Gets a user by the associated Berkeley student id. """
        return User.query.filter_by(sid=student_id).one_or_none()


class Section(db.Model):
    """ A model for sections.

    NOTE:   Currently forces the instructor to have an account first before
            sections can be stored.
    """

    __tablename__ = "sections"
    id = Column(db.Integer, primary_key=True)
    section_id = Column(db.String(255), nullable=False, unique=True)
    section_type = Column(types.Enum(SectionType), nullable=False)
    instructor_id = Column(db.Integer, ForeignKey('users.id'))
    date_rule = Column(TimeRule, nullable=False)
    location = Column(db.String(255), nullable=False)

    # Relationships
    assistants = db.relationship("Enrollment")
    attendance = db.relation("Attendance")

    def get_enrolled_assistants(self):
        """ Return all lab assistants assigned to this section. """
        return self.assistants

    def get_attendance_by_date(date):
        """ Returns the attendance for this section on DATE. """
        return [row for row in self.attendance if row.date == date]

    def is_valid_date(date):
        """ Returns true if DATE is a valid class date for this section. """
        return date_in_rule(date, date_rule)

    @staticmethod
    def lookup_by_section_id(section_id):
        """ Returns the section with the Berkeley id SECTION_ID. """
        return Section.query.filter_by(section_id=section_id).one_or_none()

    @staticmethod
    def lookup_by_instructor_id(instructor_id):
        """ Returns a list of sections associated with the instructors id. """
        return Section.query.filter_by(instructor_id=instructor_id)

    @staticmethod
    @transaction
    def load_sections_from_csv(contents):
        """ Populates the Section table from CONTENTS. Expects contents to be
        a list of dicts where each element is a row in the table.
        """
        if not check_sections_csv(contents):
            raise TypeError("Missing necessary columns")

        not_added = set()
        for entry in contents:
            section = Section.lookup_by_section_id(entry['section_id'])
            if section is None:
                user = User.lookup_by_sid(entry['instructor_id'])
                if user is None:
                    not_added.add(entry['instructor_id'])
                else:
                    logging.info("CALLING(load_sections_from_csv) creating section "
                        + entry['section_id']
                    )
                    date_rule = generate_rrule(entry['start_date'], entry['start_time'])
                    section = Section(section_id=entry['section_id'],
                        section_type=entry['section_type'],
                        instructor_id=user.id,
                        date_rule=date_rule,
                        location=entry['location']
                    )
                    db.session.add(section)
        if len(not_added) > 0:
            logging.warning("CALLING(load_sections_from_csv) missing instructors " + not_added)
            raise TypeError("Instructors do not have an account! " + not_added)


class Enrollment(db.Model):
    """ A model for enrollments. """

    __tablename__ = "enrollments"
    id = Column(db.Integer, primary_key=True)
    user_id = Column(db.Integer, ForeignKey('users.id'), nullable=False)
    section_id = Column(db.Integer, ForeignKey('sections.id'), nullable=False)

    @staticmethod
    def lookup_by_assistant_section(user_id, section_id):
        """ Returns the reference associated with USER_ID and SECTION_ID. """
        return Enrollment.query.filter_by(user_id=user_id,
                                        section_id=section_id).one_or_none()


class Attendance(db.Model):
    """ A model for tracking attendance. """

    __tablename__ = "attendance"
    id = Column(db.Integer, primary_key=True)
    date = Column(db.DateTime, nullable=False)
    user_id = Column(db.Integer, ForeignKey('users.id'), nullable=False)
    section_id = Column(db.Integer, ForeignKey('sections.id'), nullable=False)
    attendance_type = Column(types.Enum(AttendanceType), nullable=False)

    @staticmethod
    def lookup_by_assistant_section_date(user_id, section_id, date):
        """ Returns the reference associated with USER_ID on DATE for
        SECTION_ID.
        """
        return Attendance.query.filter_by(user_id=user_id,
                                            section_id=section_id,
                                            date=date).one_or_none()
