# -*- coding: utf-8 -*-
import os

os_env = os.environ

class Config(object):
    DB_NAME = os_env.get('DB_NAME')
    DB_USER = os_env.get('DB_USER')
    DB_PASS = os_env.get('DB_PASS')
    DB_HOST = os_env.get('DB_HOST')
    DB_PORT = os_env.get('DB_PORT')
    if DB_NAME is None or DB_USER is None or DB_HOST is None:
        SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/purchasing')
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
        )
    SECRET_KEY = os_env.get('PITTSBURGH-PURCHASING-SUITE_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    BROWSERID_URL = os_env.get('BROWSERID_URL')
    PER_PAGE = 50
    CITY_DOMAIN = 'pittsburghpa.gov'
    ADMIN_EMAIL = os_env.get('ADMIN_EMAIL', 'bsmithgall@codeforamerica.org')
    MAIL_DEFAULT_SENDER = 'noreply@pittsburghpurchasingsuite.com'
    MAIL_USERNAME = os_env.get('MAIL_USERNAME')
    MAIL_PASSWORD = os_env.get('MAIL_PASSWORD')
    MAIL_PORT = 587
    MAIL_USE_TLS = True

class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    FLASK_ASSETS_USE_S3 = True
    S3_BUCKET_NAME = os_env.get('S3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os_env.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os_env.get('AWS_SECRET_ACCESS_KEY')
    S3_USE_HTTPS = True
    UGLIFYJS_EXTRA_ARGS = ['-m']
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_MAX_EMAILS = 100

class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/purchasing')  # TODO: Change me
    DEBUG_TB_ENABLED = True
    BROWSERID_URL = os_env.get('BROWSERID_URL', 'http://127.0.0.1:9000')
    MAIL_SERVER = 'smtp.gmail.com'  # Use gmail in dev: https://support.google.com/mail/answer/1173270?hl=en
    ASSETS_DEBUG = True

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/purchasing_test'
    WTF_CSRF_ENABLED = False  # Allows form testing
    BROWSERID_URL = 'test'
    ASSETS_DEBUG = True
    CITY_DOMAIN = 'foo.com'
    MAIL_SUPPRESS_SEND = True
