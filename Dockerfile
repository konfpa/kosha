# syntax=docker/dockerfile:1
#
# Development stages (`tailwind`, `dev`) hold a toolchain and no source: the
# working tree is bind-mounted and everything runs as the developer's uid, so
# files written into the mount stay editable on the host.
#
# The production stage (`prod`) bakes in source, dependencies and compiled
# assets, with no toolchain, and runs as a user that owns none of it. `assets`
# and `builder` exist only to be copied out of.
#
#   docker compose build                          dev stack
#   docker compose -f compose.prod.yaml build     prod image

ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=24
ARG UV_VERSION=0.12

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv


# tailwind: the CSS watcher ===================================================

FROM node:${NODE_VERSION}-slim AS tailwind

ARG DOCKER_UID=1000
ARG DOCKER_GID=1000

WORKDIR /app

# Docker seeds the anonymous node_modules volume from the image, ownership
# included. Without this it arrives root-owned and npm cannot write to it.
RUN mkdir -p /app/node_modules && chown -R ${DOCKER_UID}:${DOCKER_GID} /app

CMD ["sh", "-c", "npm install --no-audit --no-fund && npm run watch"]


# dev: the autoreloading runserver ============================================

FROM python:${PYTHON_VERSION}-slim AS dev

COPY --from=uv /uv /uvx /usr/local/bin/

# The venv lives outside /app so the host's .venv in the bind mount, built for
# the host's platform, never collides with it. Copy mode because the cache
# volume and the venv are different filesystems, where hardlinks fail.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/cache/uv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

ARG DOCKER_UID=1000
ARG DOCKER_GID=1000

RUN mkdir -p /opt/venv /cache/uv \
    && chown -R ${DOCKER_UID}:${DOCKER_GID} /opt/venv /cache/uv

WORKDIR /app

COPY docker/dev-entrypoint.sh /usr/local/bin/dev-entrypoint

ENTRYPOINT ["dev-entrypoint"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# assets: the compiled stylesheet (build-time only) ===========================

FROM node:${NODE_VERSION}-slim AS assets

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

# The whole context rather than a list of directories, so Tailwind scans the
# same files here as in the dev watcher. A directory missing from a list would
# build fine and silently ship its elements unstyled.
COPY . .
RUN npm run build


# builder: the virtualenv (build-time only) ===================================

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=uv /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/cache/uv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/cache/uv \
    uv sync --frozen --no-dev --no-install-project


# prod: what serves ===========================================================

FROM python:${PYTHON_VERSION}-slim AS prod

# The root filesystem is read-only at run time and bytecode is compiled at
# build time, so writing .pyc would only fail on every import.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    DATABASE_URL=sqlite:////var/lib/kosha/db.sqlite3

# Fixed and high so it collides with no host account if a volume is mounted.
ARG APP_UID=10001
ARG APP_GID=10001

RUN groupadd --system --gid ${APP_GID} app \
    && useradd --system --uid ${APP_UID} --gid app --no-create-home --home-dir /app app

WORKDIR /app

# Root-owned and only readable by the app user, so a compromised worker cannot
# rewrite the code it runs or the assets it serves.
COPY --from=builder /opt/venv /opt/venv
COPY manage.py ./
COPY config/ config/
COPY templates/ templates/
COPY --from=assets /app/static/ static/
COPY docker/gunicorn.conf.py docker/

# collectstatic only needs SECRET_KEY to import settings; this one never
# reaches the image.
RUN SECRET_KEY=collectstatic python manage.py collectstatic --noinput --clear \
    && python -m compileall -q config manage.py

# The one writable path. Docker seeds a fresh named volume from this directory,
# ownership included, which is how the app user ends up able to write to it.
RUN install -d -o app -g app -m 750 /var/lib/kosha

USER app

EXPOSE 8000

CMD ["gunicorn", "--config", "docker/gunicorn.conf.py", "config.wsgi:application"]
