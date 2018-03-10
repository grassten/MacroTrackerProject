from flask import Flask, render_template, request, url_for
from app import app
import requests
from jinja2 import Template

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':

        # get user input from search bar
        food_search = request.form['search']

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
        return render_template('index.html', food_list_clean=food_list_clean)


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
                           food_carbs=food_carbs
                           )
