from app import app, db
from flask import (Flask,
                   render_template,
                   request,
                   url_for,
                   flash,
                   redirect,
                   session)
from app.forms import (SearchForm,
                       LoginForm,
                       RegistrationForm,
                       AddToDiaryForm,
                       RemoveFood,
                       DiaryDatePicker,
                       SetMacroForm,
                       SetMacroGrams)
from app.models import User, Food
import requests
from jinja2 import Template
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.urls import url_parse
from datetime import datetime, timedelta


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
@app.route('/search/<string:date>/<string:meal>', methods=['GET', 'POST'])
@login_required
def search(date=None, meal=None):
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
            max="100",
            offset="0",
            ds="sr",
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
            return render_template('search.html', date=date, meal=meal,
                                   food_list_clean=food_list_clean, form=form)


@app.route('/<string:ndbno>', methods=['GET', 'POST'])
@app.route('/<string:date>/<string:meal>/<string:ndbno>',
           methods=['GET', 'POST'])
@login_required
def get_nutrition(ndbno, meal=None, date=None):

    form1 = AddToDiaryForm()

    search_url = "https://api.nal.usda.gov/ndb/nutrients/?format=json"
    params = dict(
        api_key="ozs0jISJX6KiGzDWdXI7h9hCFBwYvk3m11HKkKbe",
        nutrients=["205", "204", "208", "203"],
        ndbno=ndbno
    )

    resp = requests.get(url=search_url, params=params)

    if "No food" in str(resp.json()):
        flash("No foods found.")
        return redirect(url_for('search'))
    else:
        food_name = resp.json()['report']['foods'][0]['name']
        food_measure = resp.json()['report']['foods'][0]['measure']
        food_cals = resp.json()['report']['foods'][0]['nutrients'][0]['value']
        food_protein = resp.json(
        )['report']['foods'][0]['nutrients'][1]['value']
        food_fat = resp.json()['report']['foods'][0]['nutrients'][2]['value']
        food_carbs = resp.json()['report']['foods'][0]['nutrients'][3]['value']

        if request.method == 'GET':
            return render_template('nutrition.html',
                                   meal=meal,
                                   date=date,
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
            if meal is None:
                meal_choice = form1.meal.data
            else:
                meal_choice = meal
            try:
                quant_choice = float(form1.quantity.data)
            except ValueError:
                flash("Please enter valid values.")
                return redirect(url_for('get_nutrition', ndbno=ndbno,
                                        meal=meal, date=date))
            if quant_choice > 10000 or meal_choice not in ("Breakfast", "Lunch", "Dinner", "Snacks"):
                flash("Please enter valid values.")
                return redirect(url_for('get_nutrition', ndbno=ndbno,
                                        meal=meal, date=date))
            if date is None:
                food = Food(food_name=food_name, count=quant_choice,
                            kcal=quant_choice * float(food_cals),
                            protein=quant_choice * float(food_protein),
                            fat=quant_choice * float(food_fat),
                            carbs=quant_choice * float(food_carbs),
                            unit=food_measure, meal=meal_choice,
                            ndbno=ndbno, user_id=current_user.get_id())
            else:
                food = Food(food_name=food_name, count=quant_choice,
                            kcal=quant_choice * float(food_cals),
                            protein=quant_choice * float(food_protein),
                            fat=quant_choice * float(food_fat),
                            carbs=quant_choice * float(food_carbs),
                            unit=food_measure, meal=meal_choice,
                            date=date, ndbno=ndbno, user_id=current_user.get_id())
            db.session.add(food)
            db.session.commit()
            return redirect(url_for('diary', date_pick=date))


@app.route('/diary', methods=['GET', 'POST'])
@app.route('/diary/<string:date_pick>', methods=['GET', 'POST'])
@login_required
def diary(date_pick=datetime.now().strftime('%B %d, %Y')):

    form = RemoveFood()
    form2 = DiaryDatePicker()

    session.pop('_flashes', None)

    form2.date.data = date_pick

    foods = Food.query.filter_by(user_id=current_user.get_id(), date=date_pick)
    user = User.query.filter_by(id=current_user.get_id()).first()

    # this only called if user clicks forward, backward, or tries to remove
    if request.method == 'POST':
        # if user clicks an "X" button to remove food from diary,
            # get the Food table row id for selected food
            # get the user ID from the Food table for the selected row
            # if the selected row user ID matches the user executing action
                # remove row from Food table
                # commit changes
            # else
                # do not allow user to make changes
        if request.form["action"] == "remove":
            remove_id = form.entry_id.data
            user_id_for_row = Food.query.filter_by(
                id=remove_id).first().user_id
            if str(user_id_for_row) == current_user.get_id():
                Food.query.filter_by(id=remove_id).delete()
                db.session.commit()
            else:
                flash("Diary entry not found.")

        # if the user clicks back, subtract one from date to get previous date
        if request.form["action"] == "back":
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') -
                         timedelta(days=1)).strftime('%B %d, %Y')

        # if the user clicks forward, add one to date to get next date
        if request.form["action"] == "forward":
            date_pick = (datetime.strptime(form2.date.data, '%B %d, %Y') +
                         timedelta(days=1)).strftime('%B %d, %Y')

        # redirect back to diary; if date is today, exclude ugliness from URL
        todays_date = datetime.now().strftime('%B %d, %Y')
        if date_pick == todays_date:
            return redirect(url_for('diary'))
        else:
            return redirect(url_for('diary', date_pick=date_pick))

    meals = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
    total_cals = {'Breakfast': 0,
                  'Lunch': 0,
                  'Dinner': 0,
                  'Snacks': 0,
                  'total': 0}
    total_carbs = {'Breakfast': 0,
                   'Lunch': 0,
                   'Dinner': 0,
                   'Snacks': 0,
                   'total': 0}
    total_protein = {'Breakfast': 0,
                     'Lunch': 0,
                     'Dinner': 0,
                     'Snacks': 0,
                     'total': 0}
    total_fat = {'Breakfast': 0,
                 'Lunch': 0,
                 'Dinner': 0,
                 'Snacks': 0,
                 'total': 0}

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

    return render_template('diary.html', foods=foods, user=user, form=form,
                           form2=form2, total_fat=total_fat,
                           total_cals=total_cals, total_carbs=total_carbs,
                           total_protein=total_protein, date_pick=date_pick)


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


@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route('/profile/macrosgrams', methods=['GET', 'POST'])
def macros_grams():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=current_user.get_id()).first()
        form = SetMacroGrams(calories=user.calories_goal)

        if request.method == 'GET':
            return render_template('macros_grams.html', user=user, form=form)

        if request.method == 'POST':
            user.carbs_grams = form.carbs.data
            user.fat_grams = form.fat.data
            user.protein_grams = form.protein.data
            user.calories_goal = (form.carbs.data * 4) + \
                (form.fat.data * 9) + (form.protein.data * 4)
            db.session.commit()
            flash("Macros updated.")
            return redirect(url_for('macros_grams'))


@app.route('/profile/macrospercent', methods=['GET', 'POST'])
def macros_percent():
    if current_user.is_authenticated == False:
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=current_user.get_id()).first()
        form = SetMacroForm(calories=user.calories_goal,
                            fat=float(user.fat_goal),
                            carbs=float(user.carb_goal),
                            protein=float(user.protein_goal))

        if request.method == 'GET':
            return render_template('macros_percent.html', user=user, form=form)

        if request.method == 'POST':
            try:
                # server-side input validation
                # check form values convert to float successfully
                # check macros add up to 100% of calories
                # check macro percentages chosen are among available
                sum_macro_percents = (float(form.protein.data) +
                                      float(form.fat.data) +
                                      float(form.carbs.data))
                valid_percents = [.05, .1, .15, .2, .25,
                                  .3, .35, .4, .45, .5, .55, .6,
                                  .65, .7, .75, .8, .85, .9]
                if not (float(form.protein.data) in valid_percents
                        and float(form.fat.data) in valid_percents
                        and float(form.carbs.data) in valid_percents):
                    flash("Error: Please enter valid values.")
                    return redirect(url_for('macros_percent'))
                if sum_macro_percents != 1.00:
                    flash("Values did not add up to 100%: try again!")
                    return redirect(url_for('macros_percent'))
            except ValueError:
                flash("Error: Please enter valid values.")
                return redirect(url_for('macros_percent'))
            else:
                # update db values
                try:
                    user.calories_goal = int(form.calories.data)
                except ValueError:
                    flash('Please enter valid calorie value.')
                    return redirect(url_for('macros_percent'))
                user.protein_goal = form.protein.data
                user.fat_goal = form.fat.data
                user.carb_goal = form.carbs.data
                user.protein_grams = int(
                    "%.0f" % ((float(user.calories_goal) * float(user.protein_goal)) / 4))
                user.fat_grams = int(
                    "%.0f" % ((float(user.calories_goal) * float(user.fat_goal)) / 9))
                user.carbs_grams = int(
                    "%.0f" % ((float(user.calories_goal) * float(user.carb_goal)) / 4))
                db.session.commit()

                flash("Macro targets updated.")
                return redirect(url_for('macros_percent'))


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
