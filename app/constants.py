from datetime import timedelta

import dateutil.parser as dp
import enum

# Google Sign-in related constants
GOOGLE_OAUTH_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# Date formats
DATE_FORMAT_STANDARD = "%m/%d/%Y at %I:%M %p"
DATE_FORMAT_CHECK_IN = "%A %m/%d at %I:00 %p"
DATE_FORMAT_ANNOUNCEMENT = "posted on %m/%d/%Y at %I:%M %p"

# The time for which lab assistants can check in for a lab
CHECK_IN_RANGE = timedelta(days=7)

# Constants related to the length of the semester
SEMESTER_START = dp.parse("8/15/2016")
SEMESTER_LENGTH = 15


class AccessLevel(enum.Enum):
    """ Different privilege levels for the application. """

    ASSISTANT = "lab assistant"
    STAFF = "course staff"
    ADMIN = "administrator"


class SectionType(enum.Enum):
    """ The types of sections assistants can assist. """

    LAB = "LAB"
    OFFICE_HOUR = "OFFICE HOURS"


class AttendanceType(enum.Enum):
    """ A lab assistant can only be present at lab or be absent. """

    ABSENT = "absent"
    PRESENT = "present"
    UNMARKED = "unmarked"
