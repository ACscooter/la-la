import dateutil.rrule as dr
import dateutil.parser as dp
import dateutil.relativedelta as drel

from app.constants import NUMBER_OF_SECTIONS

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

    NOTE:   Dates are expected in MM/DD/YYYY format
    """
    start = dp.parse("{0} {1}".format(start_date, start_time))
    return dr.rrule(dr.WEEKLY, dtstart=start, count=NUMBER_OF_SECTIONS)
