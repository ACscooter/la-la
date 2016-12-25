from flask_wtf import Form
from wtforms import (StringField, BooleanField)
from wtforms.validators import DataRequired

class LoginForm(Form):
    """ A WTForm for logging in. Login facilitated by OpenID for now.

    TODO:   Integrate Google authentication.
    """

    username = StringField('username', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)
