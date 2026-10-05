"""
Django settings for kosha.

Every deployment-specific value is read from the environment, optionally
loaded from a `.env` file at the project root. See `.env.example` for the
full list of variables and what they do.

https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# Core

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "axes",
    "apps.accounts",
    "apps.ui",
]

MIDDLEWARE = [
    "config.health.healthz_middleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.sessions.max_age_middleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database and cache

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

CACHES = {
    "default": env.cache("CACHE_URL", default="locmemcache://"),
}


# Authentication

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "home"

LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Login lockout (django-axes)

AXES_FAILURE_LIMIT = 5

AXES_COOLOFF_TIME = 1

AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]

AXES_RESET_ON_SUCCESS = True

AXES_LOCKOUT_TEMPLATE = "registration/lockout.html"

AXES_USERNAME_CALLABLE = "apps.accounts.lockout.username"

AXES_CLIENT_IP_CALLABLE = "apps.accounts.lockout.client_ip"

TRUST_X_FORWARDED_FOR = env.bool("TRUST_X_FORWARDED_FOR", default=False)


# Internationalization

LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en-us")

TIME_ZONE = env.str("TIME_ZONE", default="UTC")

USE_I18N = True

USE_TZ = True


# Static files, served by WhiteNoise

STATIC_URL = env.str("STATIC_URL", default="static/")

STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "staticfiles")

STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Email

# django-environ parses EMAIL_URL into legacy EMAIL_* keys; Django 6.1 wants
# MAILERS OPTIONS instead. Unset values are dropped because non-SMTP backends
# reject options they don't recognise.
_email = env.email_url("EMAIL_URL", default="consolemail://")
_email_options = {
    "host": _email["EMAIL_HOST"],
    "port": _email["EMAIL_PORT"],
    "username": _email["EMAIL_HOST_USER"],
    "password": _email["EMAIL_HOST_PASSWORD"],
    "use_tls": _email.get("EMAIL_USE_TLS"),
    "use_ssl": _email.get("EMAIL_USE_SSL"),
    "file_path": _email["EMAIL_FILE_PATH"],
}

MAILERS = {
    "default": {
        "BACKEND": _email["EMAIL_BACKEND"],
        "OPTIONS": {key: value for key, value in _email_options.items() if value},
    },
}

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

SERVER_EMAIL = env.str("SERVER_EMAIL", default="root@localhost")

ADMINS = env.list("ADMINS", default=[])


# HTTPS and security headers. Defaults are strict whenever DEBUG is off.

if env.bool("SECURE_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)

CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)

SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)


# Sessions. Both ages slide forward on every request; SESSION_MAX_AGE is an
# absolute cap from login enforced by apps.accounts.sessions.max_age_middleware.

SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=30 * 24 * 60 * 60)

SESSION_SHORT_AGE = env.int("SESSION_SHORT_AGE", default=12 * 60 * 60)

SESSION_MAX_AGE = env.int("SESSION_MAX_AGE", default=90 * 24 * 60 * 60)
