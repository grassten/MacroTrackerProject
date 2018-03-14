from flask import Flask, render_template, request, url_for, flash, redirect
from app import app, db
import requests
from jinja2 import Template
from app.forms import SearchForm, LoginForm, RegistrationForm
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.urls import url_parse
from app.models import User, Food


@app.route('/')
@login_required
def home():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    if request.method == 'GET':
        return render_template('search.html', form=form)

    if request.method == 'POST':

        # get user input from search bar
        food_search = form.search.data

        # build API URL to search for food
        search_url = "https://api.nal.usda.gov/ndb/search/?format=json"
        params = dict(
            q=food_search,
            sort="r",
            max="10",
            offset="0",
            api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe"
        )

        # build list of tuples w/ name of food and associated ndbno (unique ID)
        resp = requests.get(url=search_url, params=params)

        food_list = resp.json()['list']['item']
        food_list_clean = []

        for i in food_list:
            food_list_clean.append((i['name'], i['ndbno']))

        # return list of food to web page
        return render_template('search.html', food_list_clean=food_list_clean, form=form)


@app.route('/<string:ndbno>')
def get_nutrition(ndbno):
    url = "https://api.nal.usda.gov/ndb/nutrients/?format=json"
    params = dict(
        api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe",
        nutrients=["205", "204", "208", "203"],
        ndbno=ndbno
    )

    resp = requests.get(url=url, params=params)

    food_name = resp.json()['report']['foods'][0]['name']
    food_measure = resp.json()['report']['foods'][0]['measure']
    food_cals = resp.json()['report']['foods'][0]['nutrients'][0]['value']
    food_protein = resp.json()['report']['foods'][0]['nutrients'][1]['value']
    food_fat = resp.json()['report']['foods'][0]['nutrients'][2]['value']
    food_carbs = resp.json()['report']['foods'][0]['nutrients'][3]['value']

    return render_template('nutrition.html',
                           food_name=food_name,
                           food_measure=food_measure,
                           food_cals=food_cals,
                           food_protein=food_protein,
                           food_fat=food_fat,
                           food_carbs=food_carbs,
                           ndbno=ndbno
                           )


@app.route('/diary')
def diary(username):
    user = User.query.filter_by(username=username).first_or_404()
    food = Food.query.filter_by(user_id=1)

    return render_template('diary.html', food=food)


def addfood():
    ndbno = request.form.get("ndbno")

    url = "https://api.nal.usda.gov/ndb/nutrients/?format=json"
    params = dict(
        api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe",
        nutrients=["205", "204", "208", "203"],
        ndbno=ndbno
    )

    resp = requests.get(url=url, params=params)

    food_name = resp.json()['report']['foods'][0]['name']
    food_measure = resp.json()['report']['foods'][0]['measure']
    food_cals = resp.json()['report']['foods'][0]['nutrients'][0]['value']
    food_protein = resp.json()['report']['foods'][0]['nutrients'][1]['value']
    food_fat = resp.json()['report']['foods'][0]['nutrients'][2]['value']
    food_carbs = resp.json()['report']['foods'][0]['nutrients'][3]['value']

    food = Food(food_name=food_name, kcal=food_cals, protein=food_protein, fat=food_fat, carbs=food_carbs, meal="breakfast")
    db.session.add(food)
    db.session.commit()

    return render_template('diary.html', user=user, food=food)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    # logout_user is a flask_login function
    logout_user()
    return redirect(url_for('home'))
