#!/usr/bin/env bash
set -o errexit

# install deps
pip install -r requirements.txt

# collect static files (if you have static files)
python manage.py collectstatic --no-input

# run migrations
python manage.py migrate
