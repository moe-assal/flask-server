from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Length


class NotificationForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired()], widget=TextArea())
    recipient_id = StringField('Recipient ID', validators=[DataRequired(), Length(min=5, max=5)])
    submit = SubmitField('Send')
