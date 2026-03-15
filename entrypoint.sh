#!/bin/sh
# Esperar a que la DB esté lista, ejecutar migraciones y subir el server
python manage.py migrate
python manage.py runserver 0.0.0.0:8000