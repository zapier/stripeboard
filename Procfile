web: gunicorn stripeboard.wsgi:application -b 0.0.0.0:$PORT
celeryd: python manage.py celeryd -E -B --concurrency=1 --loglevel=INFO
