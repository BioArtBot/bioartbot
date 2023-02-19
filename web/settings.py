"""Application configuration."""

import os

ANNOUNCEMENT = os.environ.get('ANNOUNCEMENT', None)

class Config(object):
    """Base configuration."""
    ENV = 'default'
    UNSECURE_DEFAULT_SECRET_KEY = 'invalid-secret-key'
    SECRET_KEY = os.environ.get('WEB_SECRET', UNSECURE_DEFAULT_SECRET_KEY)
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    MONTLY_SUBMISSION_LIMIT = int(os.environ.get('WEB_MONTHLY_SUBMISSION_LIMIT', 27))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'

    """CORS settings. Origins handled below."""
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_RESOURCES = [r"/biofoundry/*", r"/user/*"]
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(', ')

    """JWT settings."""
    UNSECURE_DEFAULT_JWT_SECRET_KEY = 'invalid-jwt-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET', UNSECURE_DEFAULT_JWT_SECRET_KEY)
    JWT_TOKEN_LOCATION = os.environ.get('JWT_TOKEN_LOCATION', 'cookies').split(', ')
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = 60*60*2 #BUG: flask-jwt-extended does not handle expired tokens gracefully. Shorten this time once it does  
    
    """Mail settings."""
    MAIL_SERVER = os.environ.get('MAIL_SERVER', None)
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS', False))
    MAIL_USE_SSL = bool(os.environ.get('MAIL_USE_SSL', False))
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', None)

    """Media bucket settings."""
    AWS_SERVER = os.environ.get('AWS_SERVER', None)
    AWS_PORT = int(os.environ.get('AWS_PORT', 4566))
    AWS_DEFAULT_REGION= os.environ.get('AWS_DEFAULT_REGION', None)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
    IMAGE_BUCKET = os.environ.get('IMAGE_BUCKET', None)

    """Logging settings."""
    LOGGING_URI = os.environ.get('LOGGING_URI', None)


class ProdConfig(Config):
    """Production configuration."""
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    JWT_COOKIE_DOMAIN = os.environ.get('JWT_COOKIE_DOMAIN', '')
    JWT_COOKIE_SECURE = os.environ.get('JWT_COOKIE_SECURE', True)
    #JWT_COOKIE_SAMESITE = "None" #Appears to not work with flask-jwt-extended v4.0.2.
    #Should upgrade, but this will also require major version change of flask, to 2.2.2
    CSP_DIRECTIVES = { #Content Security Policy
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' *.fontawesome.com *.cloudflare.com *.jsdelivr.net *.bootstrapcdn.com " + JWT_COOKIE_DOMAIN,
        'style-src': "'self' 'unsafe-inline' *.bootstrapcdn.com " + JWT_COOKIE_DOMAIN,
        'img-src': "'self' * *.amazonaws.com *.paypal.com *.paypalobjects.com " + JWT_COOKIE_DOMAIN,
        'font-src': "'self' data: *.fontawesome.com",
        'connect-src': "'self' *",
        'base-uri': "'self'",
        'form-action': "'self'",
        'frame-ancestors': "'self'",
        'worker-src': "'self'",
        'manifest-src': "'self'"
    }


class DevConfig(Config):
    """Development configuration."""
    ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CSP_DIRECTIVES = { #Content Security Policy
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' localhost *.fontawesome.com *.cloudflare.com *.jsdelivr.net *.bootstrapcdn.com",
        'style-src': "'self' 'unsafe-inline' localhost *.bootstrapcdn.com",
        'img-src': "'self' * localhost *.paypal.com *.paypalobjects.com",
        'font-src': "'self' data: *.fontawesome.com",
        'connect-src': "'self' *",
        'base-uri': "'self'",
        'form-action': "'self'",
        'frame-ancestors': "'self'",
        'worker-src': "'self'",
        'manifest-src': "'self'"
    }

class TestingConfig(Config):
    ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_TEST_URL')