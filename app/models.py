from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Column, types

from app.constants import AccessLevel

import functools
import logging

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
    def wrapper(*args, **kwds):
        try:
            value = f(*args, **kwds)
            db.session.commit()
            return value
        except Exception as e:
            logger.warning("Could not write to the DB: {}".format(e.message))
            db.session.rollback()
            raise
    return wrapper


class User(db.Model, UserMixin):
    """ A model for Users. """

    __tablename__ = "users"
    id = Column(db.Integer, primary_key=True)
    sid = Column(db.Integer, unique=True)
    gid = Column(db.Integer, nullable=False, unique=True)
    name = Column(db.String(255))
    email = Column(db.String(255), nullable=False)
    access = Column(types.Enum(AccessLevel), nullable=False)


    @staticmethod
    def lookup_by_google(google_id):
        """ Get a User with the google assigned user id. """
        return User.query.filter_by(gid=google_id).one_or_none()

    @staticmethod
    def lookup_by_id(user_id):
        """ Gets the User id by the primary key. """
        return User.query.get(user_id)
