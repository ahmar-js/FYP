"""Django's command-line utility for administrative tasks."""
import os
import sys
from threading import Timer
import webbrowser
from django.core.management import execute_from_command_line

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_.settings")
    try:
        execute_from_command_line(['manage.py', 'runserver', '8080', '--noreload'])
        # Timer(3, open_webbrowser).start()
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

def open_webbrowser():
    webbrowser.open_new('http://127.0.0.1:8080/')

if __name__ == "__main__":
    Timer(4, open_webbrowser).start()
    main()


