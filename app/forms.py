from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, HiddenField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User
from markupsafe import Markup


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')


class AddToDiaryForm(FlaskForm):
    MEAL_CHOICES = [("Breakfast", "Breakfast"), ("Lunch", "Lunch"), ("Dinner", "Dinner"), ("Snacks", "Snacks")]
    add = SubmitField('Add to Diary')
    meal = SelectField(label='Select Meal', choices=MEAL_CHOICES)


class RemoveFood(FlaskForm):
    remove = SubmitField('Remove')
    entry_id = HiddenField('')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
