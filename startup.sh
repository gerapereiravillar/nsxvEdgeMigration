#!/bin/sh
set -e

export PYTHONPATH="/home/site/wwwroot:${PYTHONPATH}"

gunicorn \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-600}" \
  --access-logfile "-" \
  --error-logfile "-" \
  apps.api.run:app
