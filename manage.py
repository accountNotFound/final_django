#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

PRODUCT_ENV = False


def main():
  """Run administrative tasks."""
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_django.settings')
  try:
    from django.core.management import execute_from_command_line
  except ImportError as exc:
    raise ImportError(
        "Couldn't import Django. Are you sure it's installed and "
        "available on your PYTHONPATH environment variable? Did you "
        "forget to activate a virtual environment?"
    ) from exc
  execute_from_command_line(sys.argv)


if __name__ == '__main__':
  root_dir = os.path.abspath(os.path.dirname(__file__))
  sys.path.append(f'{root_dir}/final_django/ie_pipeline')
  main()
