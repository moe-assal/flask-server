import secrets
import os
from PIL import Image
from white_party import app, mail
from flask_mail import Message
from flask import url_for


def save_picture(form_picture):
    while True:  # keep trying until you get a unique filename
        random_hex = secrets.token_hex(16)
        picture_filename = random_hex + '.jpg'
        picture_path = os.path.join(app.root_path, 'static\\profile-image', picture_filename)
        if not os.path.isfile(picture_path):
            break

    output_size = (128, 128)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path, format='JPEG')

    return picture_filename


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='mohammad.elassal04@gmail.com', recipients=[user.email])
    msg.body = f"""{url_for('users.reset_token', token=token, _external=True)}"""
    mail.send(msg)
