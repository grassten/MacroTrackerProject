from flask import Flask, render_template, request, url_for, flash, redirect, session
from app import app, db
import requests
from jinja2 import Template
from app.forms import SearchForm, LoginForm, RegistrationForm, AddToDiaryForm, RemoveFood, DiaryDatePicker
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.urls import url_parse
from app.models import User, Food
from datetime import datetime, timedelta


@app.route('/')
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

        if "zero results" in str(resp.json()):
            flash("No results found.")
            return redirect(url_for('search'))
        else:
            food_list = resp.json()['list']['item']
            food_list_clean = []

            for i in food_list:
                food_list_clean.append((i['name'], i['ndbno']))

            # return list of food to web page
            return render_template('search.html', food_list_clean=food_list_clean, form=form)


@app.route('/<string:ndbno>', methods=['GET', 'POST'])
@login_required
def get_nutrition(ndbno):

    form1 = AddToDiaryForm()

    url = "https://api.nal.usda.gov/ndb/nutrients/?format=json"
    params = dict(
        api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe",
        nutrients=["205", "204", "208", "203"],
        ndbno=ndbno
    )

    resp = requests.get(url=url, params=params)

    if "No food" in str(resp.json()):
        flash("No foods found.")
        return redirect(url_for('search'))
    else:
        food_name = resp.json()['report']['foods'][0]['name']
        food_measure = resp.json()['report']['foods'][0]['measure']
        food_cals = resp.json()['report']['foods'][0]['nutrients'][0]['value']
        food_protein = resp.json()['report']['foods'][0]['nutrients'][1]['value']
        food_fat = resp.json()['report']['foods'][0]['nutrients'][2]['value']
        food_carbs = resp.json()['report']['foods'][0]['nutrients'][3]['value']

        if request.method == 'GET':
            return render_template('nutrition.html',
                                   food_name=food_name,
                                   food_measure=food_measure,
                                   food_cals=food_cals,
                                   food_protein=food_protein,
                                   food_fat=food_fat,
                                   food_carbs=food_carbs,
                                   ndbno=ndbno,
                                   form1=form1,
                                   )

        if request.method == 'POST':
            meal_choice = form1.meal.data
            quant_choice = int(form1.quantity.data)

            food = Food(food_name=food_name, count=int(quant_choice), kcal=quant_choice * float(food_cals), protein=quant_choice * float(food_protein), fat=quant_choice * float(food_fat), carbs=quant_choice * float(food_carbs), unit=food_measure, meal=meal_choice, ndbno=ndbno, user_id=current_user.get_id())
            db.session.add(food)
            db.session.commit()
            return redirect(url_for('diary'))


@app.route('/diary', methods=['GET', 'POST'])
@app.route('/diary/<string:date_pick>', methods=['GET', 'POST'])
@login_required
def diary(date_pick=datetime.utcnow().strftime('%B %d, %Y')):

    form = RemoveFood()
    form2 = DiaryDatePicker()

    session.pop('_flashes', None)

    form2.date.data = date_pick

    foods = Food.query.filter_by(user_id=current_user.get_id(), date=date_pick)

    if request.method == 'POST':
        if form.remove.data and form.validate():
            remove_id = form.entry_id.data
            user_id_for_row = Food.query.filter_by(id=remove_id)[0].user_id
            if str(user_id_for_row) == current_user.get_id():
                Food.query.filter_by(id=remove_id).delete()
                db.session.commit()
            else:
                flash("Diary entry not found.")
            return redirect(url_for('diary', date_pick=date_pick))
        if form2.back.data and form2.validate():
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') - timedelta(days=1)).strftime('%B %d, %Y')
            return redirect(url_for('diary', date_pick=date_pick))
        if form2.forward.data and form2.validate():
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') + timedelta(days=1)).strftime('%B %d, %Y')
            return redirect(url_for('diary', date_pick=date_pick))

    meals = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
    total_cals = {'Breakfast': 0, 'Lunch': 0, 'Dinner': 0, 'Snacks': 0, 'total': 0}
    total_carbs = {'Breakfast': 0, 'Lunch': 0, 'Dinner': 0, 'Snacks': 0, 'total': 0}
    total_protein = {'Breakfast': 0, 'Lunch': 0, 'Dinner': 0, 'Snacks': 0, 'total': 0}
    total_fat = {'Breakfast': 0, 'Lunch': 0, 'Dinner': 0, 'Snacks': 0, 'total': 0}

    for food in foods:
        total_cals['total'] = total_cals['total'] + food.kcal
        total_carbs['total'] = total_carbs['total'] + food.carbs
        total_protein['total'] = total_protein['total'] + food.protein
        total_fat['total'] = total_fat['total'] + food.fat

        for meal in meals:
            if str(food.meal) == str(meal):
                total_cals[meal] = total_cals[meal] + food.kcal
                total_carbs[meal] = total_carbs[meal] + food.carbs
                total_protein[meal] = total_protein[meal] + food.protein
                total_fat[meal] = total_fat[meal] + food.fat

    return render_template('diary.html', foods=foods, form=form, form2=form2, total_fat=total_fat, total_cals=total_cals, total_carbs=total_carbs, total_protein=total_protein)


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
