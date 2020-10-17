#!/bin/bash

export FLASK_APP='macroapp.py'

flask db init
flask db migrate
flask db upgrade

flask run