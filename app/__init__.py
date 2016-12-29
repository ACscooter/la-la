from flask import Flask
from .config import config

app = Flask(__name__)
app.config.from_object(config['dev'])
app.secret_key = app.config['SECRET_KEY']

# Logging service setup
import logging
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

# SQL setup
from .models import db
db.init_app(app)

# LoginManager setup
from flask_login import LoginManager
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"

# Register all the blueprints
from .controllers.auth import auth
app.register_blueprint(auth, url_prefix="/auth")

from app import server
