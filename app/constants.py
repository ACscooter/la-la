import enum

# Google Sign-in related constants
GOOGLE_REDIRECT_URI = "/oauth2callback"
GOOGLE_OAUTH_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


class AccessLevel(enum.Enum):
    """ Different privilege levels for the application. """
    ASSISTANT = "lab assistant"
    STAFF = "course staff"
    INSTRUCTOR = "instructor"
