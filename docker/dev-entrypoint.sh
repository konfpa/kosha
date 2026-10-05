#!/bin/sh
# Runs on every start because the lockfile and migrations live in the bind
# mount: pulling a branch that changes either should not need an image rebuild.
set -eu

uv sync --frozen
python manage.py migrate --noinput

exec "$@"
