from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Column, types
from constants import AccessLevel


import functools


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
            # TODO Log e
            db.session.rollback()
            raise
    return wrapper


class User(db.Model, UserMixin):
    """ A model for Users. """

    __tablename__ = "users"
    id = Column(db.Integer, primary_key=True, nullable=False)
    sid = Column(db.Integer, nullable=False, unique=True)
    googleuser = Column(db.Integer, nullable=False, unique=True)
    name = Column(db.String(255))
    email = Column(db.String(255), nullable=False)
    privilege = Column(types.Enum(AccessLevel), nullable=False)



    # add announcment
    # add
