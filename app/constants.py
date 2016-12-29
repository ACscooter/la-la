from datetime import timedelta

import enum

# Google Sign-in related constants
GOOGLE_OAUTH_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

# The number of sections in each semester
NUMBER_OF_SECTIONS = 15

# The time for which lab assistants can check in for a lab
CHECK_IN_RANGE = timedelta(days=7)


class AccessLevel(enum.Enum):
    """ Different privilege levels for the application. """

    ASSISTANT = "lab assistant"
    STAFF = "course staff"
    ADMIN = "administrator"


class SectionType(enum.Enum):
    """ The types of sections assistants can assist. """

    LAB = "lab"
    OFFICE_HOUR = "office hour"


class AttendanceType(enum.Enum):
    """ A lab assistant can only be present at lab or be absent. """

    ABSENT = "absent"
    PRESENT = "present"
