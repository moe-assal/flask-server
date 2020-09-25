from datetime import timedelta
import json


with open('/etc/config.json') as config_file:
    config = json.load(config_file)

class Config:
    SECRET_KEY = config.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_BINDS = {
        'laws': 'sqlite:///database/laws.db',
        'comments': 'sqlite:///database/comments.db',
        'proposals': 'sqlite:///database/proposals.db',
        'law_votes_cast': 'sqlite:///database/law_vote_cast.db',
        'configuration_db': 'sqlite:///database/configuration.db',
        'notification_db': 'sqlite:///database/notification.db',
        'volunteer_db': 'sqlite:///database/volunteer.db'
    }
    WHOOSH_BASE = 'white_party/database/whoosh'
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = config.get('MAIL_USER')
    MAIL_PASSWORD = config.get('MAIL_PASSWORD')
    if not MAIL_PASSWORD or not MAIL_USERNAME or not SECRET_KEY:
        print(MAIL_USERNAME, MAIL_PASSWORD, SECRET_KEY)
        raise KeyError('Please initialize configuration variables')

    TALISMAN_CSP = {
        'default-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'cdnjs.cloudflare.com',
            'kit.fontawesome.com',
            'code.jquery.com',
            'stackpath.bootstrapcdn.com',
            'fonts.googleapis.com',
            'kit-free.fontawesome.com',
            'fonts.gstatic.com'
            ]
        }
