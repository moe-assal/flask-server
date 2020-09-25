from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired


class LawForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    law = StringField('Law', validators=[DataRequired()], widget=TextArea())
    explanation = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')


class EditLawForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    law = StringField('Law', validators=[DataRequired()], widget=TextArea())
    explanation = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')


class TranslateLawForm(FlaskForm):
    title_arabic = StringField('Title', validators=[DataRequired()])
    info_arabic = StringField('Law', validators=[DataRequired()], widget=TextArea())
    explanation_arabic = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')
