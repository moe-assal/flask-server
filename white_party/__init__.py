"""
Reinitialization:
- ALL DATABASES SHOULD BE CLEARED
- use helper.py file to reinitialize databases and configuration
- set moderation to be for everyone in global_utilities.py
- comment first 3 lines in signup route in Users/routes.py and add if statement to insure 'user' is in session
- create user with membership_id=xyz
- set moderation to users with membership_id==xyz
"""
from flask_talisman import Talisman
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from white_party.configuration import Config
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)


# used to hash passwords
crypt = Bcrypt(app)

# security
csrf_token = CSRFProtect(app)
Talisman(app, content_security_policy=Config.TALISMAN_CSP)

db = SQLAlchemy(app)
db.create_all()

mail = Mail(app)


from white_party.Users.routes import users
from white_party.Laws.routes import laws
from white_party.Main.routes import main
from white_party.Proposals.routes import proposals
from white_party.errors.routes import errors
from white_party.tasks.routes import tasks

app.register_blueprint(users)
app.register_blueprint(laws)
app.register_blueprint(main)
app.register_blueprint(proposals)
app.register_blueprint(errors)
app.register_blueprint(tasks)


@app.before_request
def before_request():
    """
    This might be (probably) not necessary after launch
    :return:
    """
    if 'user' in session:
        if session['user'] is None:
            session.pop("user", None)

    return


@app.route('/robots.txt')
def static_from_root():
    return app.send_static_file(filename='robots.txt')
