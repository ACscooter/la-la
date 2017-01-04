from datetime import datetime

from app.utils import get_week_of



# create a connection to the database

# initialize a bunch of unmarked attendance entries in the attendance table

def create_unmarked_attendance(date=datetime.now()):
    """ Creates unmarked attendance entries for all assistants for the week
    containing DATE.
    """
    start, end = get_week_of(date)
