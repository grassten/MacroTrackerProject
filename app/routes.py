from app import app, db
from flask import render_template, request, url_for, flash, redirect, session
from app.forms import (
    SearchForm,
    LoginForm,
    RegistrationForm,
    AddToDiaryForm,
    RemoveFood,
    DiaryDatePicker,
    SetMacroForm,
    SetMacroGrams,
    QuickAddCals,
    CopyMealForm,
)
from app.models import User, Food, DiaryEntries
import requests
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm.session import make_transient


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
@app.route("/search/<string:date>/<string:meal>", methods=["GET", "POST"])
@login_required
def search(date=None, meal=None):
    form = SearchForm()

    if request.method == "GET":
        food_list_clean = []
        recent_foods = (
            DiaryEntries.query.filter_by(user_id=current_user.get_id())
            .order_by(desc(DiaryEntries.date))
            .group_by(DiaryEntries.food_name)
        )

        for food in recent_foods:
            food_list_clean.append((food.food_name, food.id))

        return render_template(
            "search.html",
            form=form,
            food_list_clean=food_list_clean,
            recent_list=True,
            date=date,
            meal=meal,
        )

    if request.method == "POST":
        if request.form["action"] == "multiadd":
            if meal is None:
                meal = request.form.get("mealselect")
            food_ids = request.form.getlist("selected")
            for food_id in food_ids:
                food = Food.query.filter_by(id=food_id).first()
                entry = DiaryEntries(
                    description=food.description,
                    calories=food.calories,
                    protein=food.protein,
                    fat=food.fat,
                    carbs=food.carbs,
                    unit=food.unit,
                    amount=food.amount,
                    meal=meal,
                    count=food.count,
                    date=date,
                    user_id=current_user.get_id(),
                )
                db.session.add(entry)
                db.session.commit()
            return redirect(url_for("diary", date_pick=date))

        else:
            food_search = form.search.data
            if food_search == "":
                return redirect(url_for("search", date=date, meal=meal))
            resp = Food.query.filter_by(description=food_search)
            if "zero results" in str(resp.json()):
                flash("No results found.")
                return redirect(url_for("search"))
            return render_template(
                "search.html",
                date=date,
                meal=meal,
                food_list_clean=[(i.description, i.id) for i in resp],
                form=form,
                recent_list=False,
            )


@app.route("/food/<string:ndbno>", methods=["GET", "POST"])
@app.route("/food/<string:date>/<string:meal>/<string:ndbno>", methods=["GET", "POST"])
@login_required
def get_nutrition(id, meal=None, date=datetime.now()):
    form1 = AddToDiaryForm()
    resp = Food.query.filter_by(id=id).first()
    if not resp:
        flash("No foods found.")
        return redirect(url_for("search"))
    food_name = resp.description
    food_unit = resp.unit
    food_amount = resp.amount
    food_cals = resp.calories
    food_protein = resp.protein
    food_fat = resp.fat
    food_carbs = resp.carbs
    if request.method == "GET":
        return render_template(
            "nutrition.html",
            meal=meal,
            date=date,
            food_name=food_name,
            food_measure=f"{food_amount}{food_unit}",
            food_cals=food_cals,
            food_protein=food_protein,
            food_fat=food_fat,
            food_carbs=food_carbs,
            form1=form1,
        )

    if request.method == "POST":
        if meal is None:
            meal_choice = form1.meal.data
        else:
            meal_choice = meal
        try:
            quant_choice = float(form1.quantity.data)
        except Exception:
            flash("Please enter valid values.")
            return redirect(url_for("get_nutrition", id=id, meal=meal, date=date))
        else:
            if quant_choice > 10000 or meal_choice not in (
                "Breakfast",
                "Lunch",
                "Dinner",
                "Snacks",
            ):
                flash("Please enter valid values.")
                return redirect(
                    url_for("get_nutrition", id=id, meal=meal, date=date)
                )
            entry = DiaryEntries(
                description=food_name,
                calories=quant_choice * float(food_cals),
                protein=quant_choice * float(food_protein),
                fat=quant_choice * float(food_fat),
                carbs=quant_choice * float(food_carbs),
                unit=food_unit,
                amount=food_amount,
                meal=meal_choice,
                count=quant_choice,
                date=date,
                user_id=current_user.get_id(),
            )
            db.session.add(entry)
            db.session.commit()
            return redirect(url_for("diary", date_pick=date))


@app.route("/diary", methods=["GET", "POST"])
@app.route("/diary/<string:date_pick>", methods=["GET", "POST"])
@login_required
def diary(date_pick=datetime.now().strftime("%B %d, %Y")):
    form = RemoveFood()
    form2 = DiaryDatePicker()
    if request.method == "GET":
        try:
            datetime.strptime(date_pick, "%B %d, %Y")
        except ValueError:
            return redirect(url_for("diary"))
        session.pop("_flashes", None)
        form2.date.data = date_pick
        entries = DiaryEntries.query.filter_by(user_id=current_user.get_id(), date=date_pick)
        user = User.query.filter_by(id=current_user.get_id()).first()

        meals = {"Breakfast": 0, "Lunch": 0, "Dinner": 0, "Snacks": 0, "total": 0}
        total_cals = dict(meals)
        total_carbs = dict(meals)
        total_protein = dict(meals)
        total_fat = dict(meals)

        for entry in entries:
            total_cals["total"] = total_cals["total"] + entry.calories
            total_carbs["total"] = total_carbs["total"] + entry.carbs
            total_protein["total"] = total_protein["total"] + entry.protein
            total_fat["total"] = total_fat["total"] + entry.fat

            for meal in meals:
                if str(entry.meal) == str(meal):
                    total_cals[meal] = total_cals[meal] + entry.calories
                    total_carbs[meal] = total_carbs[meal] + entry.carbs
                    total_protein[meal] = total_protein[meal] + entry.protein
                    total_fat[meal] = total_fat[meal] + entry.fat

        return render_template(
            "diary.html",
            foods=entries,
            user=user,
            form=form,
            form2=form2,
            total_fat=total_fat,
            total_cals=total_cals,
            total_carbs=total_carbs,
            total_protein=total_protein,
            date_pick=date_pick,
        )
    if request.method == "POST":
        if request.form["action"] == "remove":
            remove_id = form.entry_id.data
            user_id_for_row = DiaryEntries.query.filter_by(id=remove_id).first().user_id
            if str(user_id_for_row) == current_user.get_id():
                DiaryEntries.query.filter_by(id=remove_id).delete()
                db.session.commit()
            else:
                flash("Cannot access this entry.")
        elif request.form["action"] == "back":
            date_pick = (
                datetime.strptime(form2.date.data, "%B %d, %Y") - timedelta(days=1)
            ).strftime("%B %d, %Y")
        elif request.form["action"] == "forward":
            date_pick = (
                datetime.strptime(form2.date.data, "%B %d, %Y") + timedelta(days=1)
            ).strftime("%B %d, %Y")
        todays_date = datetime.now().strftime("%B %d, %Y")
        if date_pick == todays_date:
            return redirect(url_for("diary"))
        else:
            return redirect(url_for("diary", date_pick=date_pick))


@app.route("/diary/quickadd/<string:date>/<string:meal>", methods=["GET", "POST"])
@login_required
def quickadd(date=datetime.now().strftime("%B %d, %Y"), meal=None):
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = QuickAddCals()

    if request.method == "GET":
        return render_template("quickadd.html", user=user, form=form)

    if request.method == "POST":
        try:
            float(form.calories.data)
            float(form.carbs.data)
            float(form.fat.data)
            float(form.protein.data)
        except:
            flash("Please enter valid numbers.")
        else:
            entry = DiaryEntries(
                description="Quick Add",
                calories=form.calories.data,
                protein=form.protein.data,
                fat=form.fat.data or 0,
                carbs=form.carbs.data or 0,
                unit=None,
                amount=None,
                meal=meal,
                count=1,
                date=date,
                user_id=current_user.get_id(),
            )
            db.session.add(entry)
            db.session.commit()
        return redirect(url_for("diary", date_pick=date))


@app.route("/diary/copyto/<string:date>/<string:meal>", methods=["GET", "POST"])
@login_required
def copyto(date, meal):
    form = CopyMealForm()
    if request.method == "GET":
        return render_template("copyto.html", form=form)
    if request.method == "POST":
        copy_to_date = form.dt.data.strftime("%B %d, %Y")
        copy_to_meal = form.meal_select.data
        copy_meal_items = DiaryEntries.query.filter_by(
            user_id=current_user.get_id(), date=date, meal=meal
        )
        for row in copy_meal_items:
            db.session.expunge(row)
            make_transient(row)
            row.id = None
            row.meal = copy_to_meal
            row.date = copy_to_date
            db.session.add(row)
        db.session.commit()
        return redirect(url_for("diary", date_pick=copy_to_date))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash("Invalid username or password.")
                return redirect(url_for("login"))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("diary")
            return redirect(next_page)
        return render_template("login.html", form=form)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/profile/macrosgrams", methods=["GET", "POST"])
@login_required
def macros_grams():
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = SetMacroGrams(calories=user.calories_goal)
    if request.method == "GET":
        return render_template("macros_grams.html", user=user, form=form)
    if request.method == "POST":
        try:
            float(form.carbs.data)
            float(form.fat.data)
            float(form.protein.data)
        except:
            flash("Please enter valid numbers.")
        else:
            user.carbs_grams = form.carbs.data
            user.fat_grams = form.fat.data
            user.protein_grams = form.protein.data
            user.calories_goal = (
                (form.carbs.data * 4) + (form.fat.data * 9) + (form.protein.data * 4)
            )
            db.session.commit()
            flash("Macros updated.")
        return redirect(url_for("macros_grams"))


@app.route("/profile/macrospercent", methods=["GET", "POST"])
@login_required
def macros_percent():
    user = User.query.filter_by(id=current_user.get_id()).first()
    form = SetMacroForm(
        calories=user.calories_goal,
        fat=float(user.fat_goal),
        carbs=float(user.carb_goal),
        protein=float(user.protein_goal),
    )
    if request.method == "GET":
        return render_template("macros_percent.html", user=user, form=form)
    if request.method == "POST":
        valid_percents = [
            0.05,
            0.1,
            0.15,
            0.2,
            0.25,
            0.3,
            0.35,
            0.4,
            0.45,
            0.5,
            0.55,
            0.6,
            0.65,
            0.7,
            0.75,
            0.8,
            0.85,
            0.9,
        ]
        try:
            sum_macro_percents = (
                float(form.protein.data) + float(form.fat.data) + float(form.carbs.data)
            )
            if not (
                float(form.protein.data) in valid_percents
                and float(form.fat.data) in valid_percents
                and float(form.carbs.data) in valid_percents
            ):
                flash("Error: Please enter valid values.")
                return redirect(url_for("macros_percent"))
            if sum_macro_percents != 1.00:
                flash("Values did not add up to 100%: try again!")
                return redirect(url_for("macros_percent"))
        except Exception:
            flash("Error: Please enter valid values.")
            return redirect(url_for("macros_percent"))
        else:
            try:
                user.calories_goal = int(form.calories.data)
            except Exception:
                flash("Please enter valid calorie value.")
                return redirect(url_for("macros_percent"))
            user.protein_goal = form.protein.data
            user.fat_goal = form.fat.data
            user.carb_goal = form.carbs.data
            user.protein_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.protein_goal)) / 4)
            )
            user.fat_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.fat_goal)) / 9)
            )
            user.carbs_grams = int(
                "%.0f" % ((float(user.calories_goal) * float(user.carb_goal)) / 4)
            )
            db.session.commit()

            flash("Macro targets updated.")
            return redirect(url_for("macros_percent"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    else:
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, you are now a registered user!")
            return redirect(url_for("login"))
        return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    # logout_user is a flask_login function
    logout_user()
    return redirect(url_for("home"))
