#__init__.py - imports Flask, SQLALchemy, and Flask-Admin sets them to variables,
# then imports models.py and views.py, which define the content of the website

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail

app = Flask(__name__)

app.config.from_object('web.config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)

import web.models, web.views