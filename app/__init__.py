from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('../settings.cfg')
app.secret_key = app.config['SECRET_KEY']

# SQL setup
from app import models
models.db.init_app(app)

# Register all the blueprints
from .controllers.auth import auth
app.register_blueprint(auth, url_prefix="/auth")

from app import server
