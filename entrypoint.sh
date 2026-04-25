#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import sys, os
import psycopg2
ok = False
try:
    psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB','oil_procurement'),
        user=os.getenv('POSTGRES_USER','oil_user'),
        password=os.getenv('POSTGRES_PASSWORD','oil_password'),
        host=os.getenv('POSTGRES_HOST','db'),
        port=os.getenv('POSTGRES_PORT','5432'),
    )
    ok = True
except Exception:
    ok = False
sys.exit(0 if ok else 1)
"; do
  echo "  PostgreSQL not ready — waiting..."
  sleep 2
done
echo "PostgreSQL is ready."

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Seed data only on first run (if no users exist)
python manage.py shell -c "
from core.models import CustomUser
if not CustomUser.objects.exists():
    from django.core.management import call_command
    call_command('seed_data')
"

exec gunicorn oil_procurement.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120
