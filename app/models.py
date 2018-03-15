from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    food = db.relationship('Food', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(140))
    kcal = db.Column(db.Numeric(10,0))
    protein = db.Column(db.Numeric(10,0))
    fat = db.Column(db.Numeric(10,0))
    carbs = db.Column(db.Numeric(10,0))
    meal = db.Column(db.String(64))
    ndbno = db.Column(db.String(64))
    unit = db.Column(db.String(64))
    count = db.Column(db.Numeric(10,0))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Food {}>'.format(self.food_name)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
