from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, HiddenField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User
from markupsafe import Markup
from datetime import datetime


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')


class SetMacroForm(FlaskForm):
    PERCENT_CHOICES = [(.05, "5%"),
                       (.1, "10%"),
                       (.15, "15%"),
                       (.2, "20%"),
                       (.25, "25%"),
                       (.3, "30%"),
                       (.35, "35%"),
                       (.4, "40%"),
                       (.45, "45%"),
                       (.5, "50%"),
                       (.55, "55%"),
                       (.6, "60%"),
                       (.65, "65%"),
                       (.7, "70%"),
                       (.75, "75%"),
                       (.8, "80%"),
                       (.85, "85%"),
                       (.9, "90%")]

    calories = IntegerField('Calories', validators=[DataRequired()])
    protein = SelectField('Protein', choices=PERCENT_CHOICES, validators=[DataRequired()], default=.1)
    fat = SelectField('Fat', choices=PERCENT_CHOICES, validators=[DataRequired()])
    carbs = SelectField('Carbs', choices=PERCENT_CHOICES, validators=[DataRequired()])
    change_macros = SubmitField('Update')


class AddToDiaryForm(FlaskForm):
    MEAL_CHOICES = [("Breakfast", "Breakfast"), ("Lunch", "Lunch"), ("Dinner", "Dinner"), ("Snacks", "Snacks")]
    QUANTITY_CHOICES = [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")]
    add = SubmitField('Add to Diary')
    meal = SelectField(label='Select Meal', choices=MEAL_CHOICES, validators=[DataRequired()])
    quantity = SelectField(label='Select Quantity', choices=QUANTITY_CHOICES, validators=[DataRequired()])


class DiaryDatePicker(FlaskForm):
    date = StringField(default=datetime.utcnow().strftime('%B %d, %Y'), validators=[DataRequired()])
    back = SubmitField('Back')
    forward = SubmitField('Forward')


class RemoveFood(FlaskForm):
    remove = SubmitField('X')
    entry_id = HiddenField('', validators=[DataRequired()])


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
