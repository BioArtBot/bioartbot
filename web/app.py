"""The app module, containing the app factory function."""
import os
from flask import Flask, render_template
from flask_migrate import upgrade
from sqlalchemy.exc import DBAPIError
from web.extensions import db, migrate, mail, cache, cors, jwt, argon2, talisman
from web.views import main
from web.api.user.artpiece.endpoints import artpiece_blueprint
from web.api.user.endpoints import user_blueprint
from web.api.lab_objects.endpoints import lab_object_blueprint
from web.api.biofoundry.endpoints import biofoundry_blueprint
from web.api.user.exceptions import InvalidUsage

def create_app():

    """An application factory."""
    app = Flask(__name__.split('.')[0])
    app.url_map.strict_slashes = False
    app_settings = os.getenv('APP_SETTINGS')
    app.config.from_object(app_settings)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shell_context(app)

    return app

def register_extensions(app):
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    argon2.init_app(app)
    talisman.init_app(app,
                      content_security_policy=app.config['CSP_DIRECTIVES'],
                      content_security_policy_report_only=True,
                      content_security_policy_report_uri=app.config['LOGGING_URI'],
                      force_https=True
                      )

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(main)
    app.register_blueprint(artpiece_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(lab_object_blueprint)
    app.register_blueprint(biofoundry_blueprint)

def register_errorhandlers(app):
    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = error.to_json()
        response.status_code = error.status_code
        return response

    """Catch all error handler for db"""
    @app.errorhandler(DBAPIError)
    def handle_db_error(error):
        response = "internal server error"
        return response, 500

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

def register_shell_context(app):
    @app.shell_context_processor
    def ctx():
        return {'app': app, 'db': db}

    @app.cli.command()
    def reset_db():
        db.reflect()
        db.drop_all()
        upgrade()
