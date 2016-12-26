from flask import Flask
from .controllers.auth import auth

app = Flask(__name__)
app.config.from_pyfile('../settings.cfg')
app.secret_key = app.config['SECRET_KEY']

# Register all the blueprints
app.register_blueprint(auth, url_prefix="/auth")

from app import server
