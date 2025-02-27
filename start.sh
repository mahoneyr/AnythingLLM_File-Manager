#!/bin/bash

# Apply database migrations
python manage.py migrate

# Kurzer Delay, um sicherzustellen, dass alles bereit ist
sleep 5

# Start Django-Q Cluster in the background
python manage.py qcluster &

# Start Gunicorn server
gunicorn main.wsgi:application --bind 0.0.0.0:8010
