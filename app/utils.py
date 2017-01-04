from datetime import datetime, timedelta

from app.constants import SEMESTER_LENGTH

import dateutil.rrule as dr
import dateutil.parser as dp
import dateutil.relativedelta as drel

def check_sections_csv(contents):
    """ Returns if the CSV of sections is valid. """
    return ("section_id" in contents and "section_type" in contents
            and "instructor_id" in contents
            and "start_date" in contents
            and "start_time" in contents
            and "location" in contents)

def generate_rrule(start_date, start_time):
    """ Returns the rrule associated with the section starting on START_DATE
    at START_TIME each week.dp.

    NOTE:   Dates are expected in MM/DD/YYYY format. Both are Strings.
    """
    start = dp.parse("{0} {1}".format(start_date, start_time))
    return dr.rrule(dr.WEEKLY, dtstart=start, count=SEMESTER_LENGTH)

def date_in_rule(date, date_rule):
    """ Returns if the given date is in the range of the date_rule.

    NOTE:   Assumes the type of DATE is datetime.datetime
    """
    return any(date.date() == other.date() for other in date_rule)

def date_in_rule_range(date, date_rule, range):
    """ Returns a list of dates for which date is in the range of the dates in
    date_rule.

    NOTE:   Assumes the type of DATE is datetime.datetime and type of range is
            datetime.timedelta
    """
    results = filter(lambda x : x - date <= range, date_rule)
    return list(results)

def get_week_ranges(start_date, num_weeks):
    """ Returns a list of date tuples (start, end) where start and end are the
    start date and end date of the week including and after START_DATE. The
    size of the returned list is NUM_WEEKS.

    NOTE:   START_DATE is a datetime.datetime object
    """
    prev_sunday, next_sunday = get_week_of(start_date)
    start_rule = dr.rrule(dr.WEEKLY, dtstart=prev_sunday, count=num_weeks)
    end_rule = dr.rrule(dr.WEEKLY, dtstart=next_sunday, count=num_weeks)
    return zip(start_rule, end_rule)

def get_week_of(date):
    """ Returns a tuple (start, end) where start is the sunday before and end is
    the saturday after DATE at 23:59:59.
    """
    start = date - timedelta((date.weekday() + 1) % 7)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(6)
    end = end.replace(hour=23, minute=59, second=59)
    return start, end
