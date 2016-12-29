from datetime import datetime, timedelta

from app.constants import NUMBER_OF_SECTIONS, CHECK_IN_RANGE

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
    return dr.rrule(dr.WEEKLY, dtstart=start, count=NUMBER_OF_SECTIONS)

def date_in_rule(date, date_rule):
    """ Returns if the given date is in the range of the date_rule.

    NOTE:   Assumes the type of DATE is datetime.datetime
    """
    return date in date_rule

def date_in_rule_range(date, date_rule, range):
    """ Returns a list of dates for which date is in the range of the dates in
    date_rule.

    NOTE:   Assumes the type of DATE is datetime.datetime and type of range is
            datetime.timedelta
    """
    results = filter(lambda x : x - date <= range, date_rule)
    return list(results)
