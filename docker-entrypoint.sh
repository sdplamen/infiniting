#!/bin/sh
set -e

# settings.py reads secrets (SECRET_KEY, Cloudinary, DB) from the environment,
# so these run when the container starts, not when the image is built.
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
