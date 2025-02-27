#!/bin/bash

# Führe Migrationen aus
python manage.py makemigrations
python manage.py migrate

# Starte Django Q Cluster im Hintergrund
python manage.py qcluster &
Q_PID=$!

# Starte Django Server
python manage.py runserver 0.0.0.0:${PORT:-8010} &
DJANGO_PID=$!

# Trap SIGTERM and SIGINT
trap "kill $Q_PID $DJANGO_PID" SIGTERM SIGINT

# Warte auf beide Prozesse
wait $Q_PID $DJANGO_PID
