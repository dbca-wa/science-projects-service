import logging
from logging import LogRecord
from pathlib import Path
import os
import dj_database_url
import environ

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


# Project ENV ===================================================================
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = True if os.environ.get("DJANGO_DEBUG") != "False" else False
DATABASE_URL = os.environ.get("DATABASE_URL")
ON_TEST_NETWORK = True if os.environ.get("ON_TEST_NETWORK") != "False" else False
SITE_URL_HTTP = f'https://{env("SITE_URL")}'
SECRET_KEY = env("SECRET_KEY")
EXTERNAL_PASS = env("EXTERNAL_PASS")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500  # For admin mass gen
PAGE_SIZE = 10
USER_LIST_PAGE_SIZE = 250


# Internationalization ==========================================================
TIME_ZONE = "Australia/Perth"
LANGUAGE_CODE = "en-au"
USE_I18N = True
USE_TZ = True


# Media, Roots and Storage =====================================================
ROOT_URLCONF = "config.urls"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/files/"
MEDIA_ROOT = os.path.join(BASE_DIR, "files")
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"


# Email Config =========================================================
EMAIL_HOST = "mail-relay.lan.fyi"
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
ENVELOPE_EMAIL_RECIPIENTS = [env("SPMS_MAINTAINER_EMAIL")]
ENVELOPE_USE_HTML_EMAIL = True


# Database =============================================================
DATABASES = {"default": dj_database_url.config()}

# Auth =========================================================
AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
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


# CORS and Hosts =========================================================

# /usr/src/app/backend (for getting images using PrinceXML)
PRINCE_SERVER_URL = env("PRINCE_SERVER_URL")
if not DEBUG and PRINCE_SERVER_URL == "":
    PRINCE_SERVER_URL = BASE_DIR

ALLOW_LIST = [
    "127.0.0.1",
    "localhost",
    "dbcab2c.b2clogin.com",
    "dbcab2c.onmicrosoft.com",
    "login.microsoftonline.com",
    "http://localhost",
    "http://0.0.0.0",
    "http://0.0.0.0:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
]

if not DEBUG and not PRINCE_SERVER_URL.startswith("/usr"):
    ALLOW_LIST.append(PRINCE_SERVER_URL)

ALLOW_LIST += [SITE_URL_HTTP]
# ALLOW_LIST += [env("SITE_URL")]


ALLOW_LIST_HTTP = [
    (
        item
        if item.startswith("http://") or item.startswith("https://")
        else "http://" + item
    )
    for item in ALLOW_LIST
]
ALLOWED_HOSTS = ALLOW_LIST
# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = ALLOW_LIST_HTTP
CSRF_TRUSTED_ORIGINS = ALLOW_LIST_HTTP

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "OPTIONS",
    "PUT",
    "DELETE",
]
CORS_ALLOW_HEADERS = [
    "X-CSRFToken",
    "Content-Type",
]


if DEBUG:
    SITE_URL = "127.0.0.1:3000"
else:
    SITE_URL = SITE_URL_HTTP


if DEBUG:
    INSTANCE_URL = "http://127.0.0.1:8000/"
else:
    INSTANCE_URL = SITE_URL_HTTP

CORS_ALLOWED_ORIGINS += [
    "https://dbcab2c.b2clogin.com",
    "https://dbcab2c.onmicrosoft.com",
    "https://login.microsoftonline.com",
]

CORS_ALLOWED_ORIGINS = [
    url for url in CORS_ALLOWED_ORIGINS if url.strip() and url.strip() != "http:///"
]
CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS))

# print(CORS_ALLOWED_ORIGINS)


# Application definitions ======================================================
SYSTEM_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

CUSTOM_APPS = [
    "quotes.apps.QuotesConfig",
    "common.apps.CommonConfig",
    "users.apps.UsersConfig",
    "contacts.apps.ContactsConfig",
    "medias.apps.MediasConfig",
    "agencies.apps.AgenciesConfig",
    "categories.apps.CategoriesConfig",
    "locations.apps.LocationsConfig",
    "projects.apps.ProjectsConfig",
    "communications.apps.CommunicationsConfig",
    "documents.apps.DocumentsConfig",
    "adminoptions.apps.AdminoptionsConfig",
]

INSTALLED_APPS = SYSTEM_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.dbca_middleware.DBCAMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Logs and Tracking =======================================================================
if not DEBUG:
    sentry_sdk.init(
        dsn=env("SENTRY_URL"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )


class ColoredFormatter(logging.Formatter):
    def color_string(self, string, color):
        colors = {
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "white": "\033[97m",
            "yellow": "\033[93m",
            "red": "\033[91m",
        }
        ft = f"{colors[color]}{string}\033[0m"
        return ft

    def format(self, record: LogRecord) -> str:
        log_message = super().format(record)
        level = ""
        message = ""
        time = self.formatTime(record, "%d-%m-%Y @ %H:%M:%S")
        traceback = ""
        # time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        if record.levelname == "DEBUG" or record.levelname == "INFO":
            level = self.color_string(f"[{record.levelname}] {record.message}", "white")
            message = self.color_string(log_message, "white")
        elif record.levelname == "WARNING":
            level = self.color_string(
                f"[{record.levelname}] {record.message}", "yellow"
            )
            message = self.color_string(log_message, "white")
        elif record.levelname == "ERROR":
            level = self.color_string(f"[{record.levelname}] {record.message}", "red")
            message = self.color_string(log_message, "white")

        if record.levelname == "ERROR":
            traceback += f"{record.exc_text}"

        if len(traceback) > 1 and traceback != "None":
            return f"{self.color_string(time, 'blue')} {level}\n{traceback}"
        else:
            return f"{self.color_string(time, 'blue')} {level}"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "config.settings.ColoredFormatter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "filters": [],
        }
    },
    "loggers": {
        logger_name: {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        }
        for logger_name in (
            "django",
            "django.request",
            "django.db.backends",
            "django.template",
            "core",
        )
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
}

LOGGER = logging.getLogger(__name__)
