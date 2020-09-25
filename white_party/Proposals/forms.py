from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    info = StringField('Info', validators=[DataRequired()], widget=TextArea())
    explanation = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')


class CommentForm(FlaskForm):
    comment = StringField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post')


class UpdateEditProposal(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    info = StringField('Edit Proposal', validators=[DataRequired()], widget=TextArea())
    explanation = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')


class TranslateEditProposal(FlaskForm):
    title_arabic = StringField('Title', validators=[DataRequired()], widget=TextArea())
    info_arabic = StringField('Edit Proposal', validators=[DataRequired()], widget=TextArea())
    explanation_arabic = StringField('Explanation', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Post')
