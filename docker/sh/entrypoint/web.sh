#tail -f /dev/null # If things go wrong use this to get the container up
gunicorn wsgi:application -b 0.0.0.0:8000 -w 2 --log-file=- --access-logfile=- --log-level debug --reload