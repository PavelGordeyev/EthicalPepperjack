from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired()])
    password = PasswordField('Username', validators=[
        DataRequired(),
        Length(min=8)])
    submit = SubmitField('Submit')

class SignUpForm(FlaskForm):
    f_name = StringField('First Name', validators=[
        DataRequired()])
    l_name = StringField('Last Name', validators=[
        DataRequired()])
    username = StringField('Username', validators=[
        DataRequired()])
    email = StringField('Email', validators=[
        DataRequired()])
    password = StringField('Username', validators=[
        DataRequired(),
        Length(min=8)])
    submit = SubmitField('Submit')