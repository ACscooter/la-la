from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import MetaData, Column, ForeignKey, types, create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from datetime import datetime

from app import app
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

def transaction(f):
    """ Decorator for database (session) transactions."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            value = f(*args, **kwargs)
            db.session.commit()
            return value
        except Exception as e:
            logger.warning("Could not write to the DB: {}".format(e))
            db.session.rollback()
            raise
    return wrapper

def disposable_session():
    """ Decorator for allowing disposable access to a database session. All
    wrapped functions may now use local_session as a variable.

    TODO:   Actually make this a wrapper...
    """
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    Session = sessionmaker(bind=engine)
    local_session = Session()
    return local_session


# --------------------------- USER MODEL ---------------------------


class User(db.Model, UserMixin):
    """ A model for Users. Note all arguments for SECTION_ID takes in the
    Berkeley assigned alphanumeric ID.
    """

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

    def get_sections_instructed(self):
        """ Returns all sections the user is teaching. """
        if self.access == AccessLevel.STAFF or self.access == AccessLevel.ADMIN:
            return self.sections
        return []

    def get_sections_enrolled(self):
        """ Returns a list of all sections the user is enrolled in. """
        results = set()
        if self.access == AccessLevel.ASSISTANT:
            for entry in self.enrolled:
                s = Section.query.filter_by(id=entry.section_id).one_or_none()
                if s is not None:
                    results.add(s)
                else:
                    logger.warning("Error getting enrolled section: no such section exists {0}".format(entry.section_id))
        return list(results)

    def get_all_attendances(self):
        """ Returns all attendance entries for user. """
        if self.access == AccessLevel.ASSISTANT:
            return Attendance.query.filter_by(assistant_id=self.id).all()
        return []

    def mark_unmarked(self, section_id, date):
        """ Marks the assistant as unmarked from SECTION_ID on DATE. """
        self.mark_attendance(section_id, date, AttendanceType.UNMARKED)

    def mark_present(self, section_id, date):
        """ Marks the assistant as present from SECTION_ID on DATE. """
        self.mark_attendance(section_id, date, AttendanceType.PRESENT)

    def mark_absent(self, section_id, date):
        """ Marks the assistant as absent from SECTION_ID on DATE. """
        self.mark_attendance(section_id, date, AttendanceType.ABSENT)

    @transaction
    def mark_attendance(self, section_id, date, attend):
        """ Marks the assistant as ATTEND from SECTION_ID on DATE. If element
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
        mark = None
        if attend != AttendanceType.UNMARKED:
            mark = datetime.now()
        elem = Attendance.lookup_by_assistant_section_date(self.id, section.id, date)
        if elem is None:
            elem = Attendance(assistant_id=self.id,
                mark_date=mark,
                section_id=section.id,
                section_date=date,
                attendance_type=attend
            )
            db.session.add(elem)
        else:
            elem.attendance_type = attend

    @transaction
    def enroll(self, section_id):
        """ Enrolls an assistant in a section. Note SECTION_ID is the Berkeley
        assigned section id.
        """
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
        enrollment = Enrollment.lookup_by_assistant_section(self.id, section.id)
        if enrollment is None:
            enrollment = Enrollment(user_id=self.id, section_id=section.id)
            db.session.add(enrollment)

    @staticmethod
    def all_assistants():
        """ Returns all lab assistants. """
        return User.query.filter_by(access=AccessLevel.ASSISTANT).all()

    @staticmethod
    def all_staff():
        """ Returns all staff members (including admins). """
        return User.query.filter(or_(db.users.access==AccessLevel.STAFF, db.users.access==AccessLevel.ADMIN))

    @staticmethod
    def all_admin():
        """ Returns all lab assistants. """
        return User.query.filter_by(access=AccessLevel.ADMIN).all()

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


# --------------------------- SECTION MODEL ---------------------------


class Section(db.Model):
    """ A model for sections.

    NOTE:   Currently forces the instructor to have an account first before
            sections can be stored.

    TODO:   Interface with the Attendance table here not in Users
    """

    __tablename__ = "sections"
    id = Column(db.Integer, primary_key=True)
    section_id = Column(db.String(255), nullable=False, unique=True)
    section_type = Column(types.Enum(SectionType), nullable=False)
    instructor_id = Column(db.Integer, ForeignKey('users.id'))
    date_rule = Column(db.PickleType, nullable=False)
    location = Column(db.String(255), nullable=False)

    # Relationships
    assistants = db.relationship("Enrollment")
    attendance = db.relationship("Attendance")
    instructor = db.relationship("User", back_populates="sections")

    def get_enrolled_assistants(self):
        """ Return all lab assistants assigned to this section. """
        return self.assistants

    def get_attendance_by_date(self, date):
        """ Returns the attendance for this section on DATE. """
        return [row for row in self.attendance if row.date == date]

    def is_valid_date(self, date):
        """ Returns true if DATE is a valid class date for this section. """
        return date_in_rule(date, self.date_rule)

    @transaction
    def add_section(self):
        section = Section.lookup_by_section_id(self.section_id)
        if section is not None:
            logger.warning("Cannot add duplicate section {0}".format(self.section_id))
            raise TypeError("Cannot add duplicate section")
        db.session.add(self)

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
                    logger.info("CALLING(load_sections_from_csv) creating section "
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
            logger.warning("CALLING(load_sections_from_csv) missing instructors " + not_added)
            raise TypeError("Instructors do not have an account! " + not_added)


# --------------------------- ENROLLMENT MODEL ---------------------------


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


# --------------------------- ATTENDANCE MODEL ---------------------------


class Attendance(db.Model):
    """ A model for tracking attendance. The entry requires three dates:

    -   mark_date : the date and time when the student first submits the
                    attendance entry
    -   section_date :  the date of the section the student is marking for
                    attendance
    -   confirmation_date : the date and time of when the instructor confirms
                    attendance

    Additionall requires the instructor_id for confirming the attendance.
    Initially, these fields may be NULL.
    """

    __tablename__ = "attendance"
    id = Column(db.Integer, primary_key=True)
    assistant_id = Column(db.Integer, ForeignKey('users.id'), nullable=False)
    mark_date = Column(db.DateTime)
    section_id = Column(db.Integer, ForeignKey('sections.id'), nullable=False)
    section_date = Column(db.DateTime, nullable=False)
    instructor_id = Column(db.Integer, ForeignKey('users.id'))
    confirmation_date = Column(db.DateTime)
    attendance_type = Column(types.Enum(AttendanceType), nullable=False)

    # Relationships
    section = db.relationship("Section", back_populates="attendance")


    @property
    def is_confirmed(self):
        """ Returns if this attendance entry has been confirmed by a staff
        member.
        """
        return instructor_id and confirmation_date

    @transaction
    def confirm_attendance(self, user):
        """ Confirms this attendance entry. """
        if user.access == AccessLevel.ASSISTANT:
            logger.info("Error confirming attendance for {0}: user {1} is not a staff member.".format(
                self.assistant_id,
                user.id
            ))
            raise TypeError("Cannot confirm attendance if not staff member.")
        if not (self.instructor_id is None or self.confirmation_date is None):
            logger.info("Error confirming attendance for {0}: attendance already confirmed.".format(self.assistant_id))
            raise TypeError("Attendance is already confirmed")
        self.instructor_id = user.id
        self.confirmation_date = datetime.now()

    @staticmethod
    def lookup_by_assistant_section_date(user_id, section_id, section_date):
        """ Returns the reference associated with USER_ID on DATE for
        SECTION_ID. The SECTION_ID is the sections table's primary key
        """
        return Attendance.query.filter_by(assistant_id=user_id,
                                        section_id=section_id,
                                        section_date=section_date).one_or_none()


# --------------------------- ANNOUNCEMENTS MODEL ---------------------------


class Announcement(db.Model):
    """ A model for announcements.

    NOTE:   The tags are comma separated and meant to be rendered as different
            chips in the front-end.
    """

    __tablename__ = "announcements"
    id = Column(db.Integer, primary_key=True)
    author = Column(db.Integer, ForeignKey('users.id'), nullable=False)
    date = Column(db.DateTime)
    title = Column(db.String(255), nullable=False)
    content = Column(db.Text, nullable=False)
    tags = Column(db.Text)

    def format_as_dict(self):
        """ Returns the announcement in a nice dictionary format. """
        user = User.query.filter_by(id=self.author).one_or_none()
        user_name = "admin"
        if user is not None:
            user_name = user.name
        formatted = {
            'title' : self.title,
            'author' : user_name,
            'date' : self.date,
            'content' : self.content,
            'tags' : self.tags.split(", ")
        }
        return formatted

    @staticmethod
    @transaction
    def make_announcement(user, title, content, tags=None):
        """ Makes an announcement from USER at the current time. """
        new_announcement = Announcement(
            author=user.id,
            date=datetime.now(),
            title=title,
            content=content,
            tags=tags
        )
        db.session.add(new_announcement)

    @staticmethod
    def all_announcements():
        """ Returns all announcements as a list in dict format. """
        return [entry.format_as_dict() for entry in Announcement.query.all()]

    @staticmethod
    def lookup_by_author(user_id):
        """ Returns all announcements made by USER_ID. """
        return db.session.query.filter_by(author=user_id).all()
