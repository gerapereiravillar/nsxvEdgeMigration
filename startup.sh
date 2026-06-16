#!/bin/sh
set -e

gunicorn --bind "0.0.0.0:${PORT:-${WEBSITES_PORT:-8000}}" apps.api.run:app