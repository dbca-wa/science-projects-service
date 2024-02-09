import base64
import logging
from logging import LogRecord
from pathlib import Path
import os
import environ
from datetime import timedelta
import requests

import dj_database_url
import sentry_sdk

from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# DEBUG = False if env("DEBUG") == "False" else True
DEBUG = os.environ.get("DJANGO_DEBUG") == "True"
SECRET_KEY = env("SECRET_KEY")
EXTERNAL_PASS = env("EXTERNAL_PASS")
CF_IMAGES_TOKEN = env("CF_IMAGES_TOKEN")
CF_ACCOUNT_ID = env("CF_ACCOUNT_ID")
CF_UPLOAD_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/images/v2/direct_upload"

if DEBUG:
    INSTANCE_URL = "http://127.0.0.1:8000/"
else:
    INSTANCE_URL = "https://scienceprojects-test.dbca.wa.gov.au"

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

TIME_ZONE = "Australia/Perth"
LANGUAGE_CODE = "en-au"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
WSGI_APPLICATION = "config.wsgi.application"


AUTH_USER_MODEL = "users.User"


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
    "tasks.apps.TasksConfig",
]


INSTALLED_APPS = SYSTEM_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

# APPEND_SLASH = False

ROOT_URLCONF = "config.urls"

if not DEBUG:
    # Azure db
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": env("PRODUCTION_DB_NAME"),
            "USER": env("PRODUCTION_USERNAME"),
            "PASSWORD": env("PRODUCTION_PASSWORD"),
            "HOST": env("PRODUCTION_HOST"),
            "PORT": "5432",
            "OPTIONS": {
                "options": "-c client_encoding=utf8",
            },
            "CONN_MAX_AGE": 600,
        }
    }
else:
    # Local postgres db
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": f"{env('DBNAME')}",
            "USER": f"{env('PGUSER')}",
            "PASSWORD": f"{env('PGPASS')}",
            "OPTIONS": {
                "options": "-c client_encoding=utf8",
            },
            "CONN_MAX_AGE": 600,
        }
    }

ALLOWED_HOSTS = [
    "scienceprojects-test-api.dbca.wa.gov.au",
    "scienceprojects-test.dbca.wa.gov.au",
    "cycle-test-clusterip.cycle",
    "cycle-test-frontend-clusterip.cycle",
    "127.0.0.1",
]


# Get the additional host(s) from the environment variable and split it into a list
additional_host = os.environ.get("ADDITIONAL_HOST")
if additional_host:
    additional_host_list = additional_host.split(",")
    ALLOWED_HOSTS += additional_host_list


CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
CORS_ALLOW_HEADERS = [
    "X-CSRFToken",
    "Content-Type",
]

CORS_ALLOWED_ORIGINS = [
    "https://scienceprojects-test.dbca.wa.gov.au",
    "http://scienceprojects-test.dbca.wa.gov.au",
    "https://scienceprojects-test-api.dbca.wa.gov.au",
    "http://scienceprojects-test-api.dbca.wa.gov.au",
    "https://cycle-test-clusterip.cycle",
    "http://cycle-test-clusterip.cycle",
    "https://cycle-test-frontend-clusterip.cycle",
    "http://cycle-test-frontend-clusterip.cycle",
    "https://cycle-test-clusterip.cycle:3000",
    "http://cycle-test-clusterip.cycle:3000",
    "https://cycle-test-frontend-clusterip.cycle:3000",
    "http://cycle-test-frontend-clusterip.cycle:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    # "https://*",
    # "http://*",
]

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://scienceprojects-test.dbca.wa.gov.au",
    "http://scienceprojects-test.dbca.wa.gov.au",
    "https://scienceprojects-test-api.dbca.wa.gov.au",
    "http://scienceprojects-test-api.dbca.wa.gov.au",
    "http://cycle-test-clusterip.cycle",
    "https://cycle-test-clusterip.cycle",
    "https://cycle-test-frontend-clusterip.cycle",
    "http://cycle-test-frontend-clusterip.cycle",
    "https://cycle-test-clusterip.cycle:3000",
    "http://cycle-test-clusterip.cycle:3000",
    "https://cycle-test-frontend-clusterip.cycle:3000",
    "http://cycle-test-frontend-clusterip.cycle:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    # "https://*",
    # "http://*",
]

# Get the additional url(s) from the environment variable and split it into a list
additional_url = os.environ.get("ADDITIONAL_URL")
if additional_url:
    additional_url_list = additional_url.split(",")
    CORS_ALLOWED_ORIGINS += additional_url_list
    CSRF_TRUSTED_ORIGINS += additional_url_list


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

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)


DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500  # For admin mass gen

if not DEBUG:
    sentry_sdk.init(
        dsn="https://cdcf29f929f0933f07cd883c3690fe41@o4504491005902848.ingest.sentry.io/4506080017317888",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/files/"
MEDIA_ROOT = os.path.join(BASE_DIR, "files")
# MEDIA_ROOT = "/usr/src/app/backend/files"

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# STORAGES = {
#     # Enable WhiteNoise's GZip and Brotli compression of static assets:
#     # https://whitenoise.readthedocs.io/en/latest/django.html#add-compression-and-caching-support
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
#     "files": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
#     "default": {
#         "ENGINE": "django.core.files.storage.FileSystemStorage",
#         "OPTIONS": {
#             # Storage-specific options (if any)
#         },
#     },
# }

# if not DEBUG:  # Whitenoise brotli config for static files in production ()
#     # Django < 4.2
#     STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

#     # Django 4.2+
#     STORAGES = {
#         # ...
#         "staticfiles": {
#             "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#         },
#     }


PAGE_SIZE = 10
USER_LIST_PAGE_SIZE = 250


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


# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#         },
#     },
#     "root": {
#         "handlers": ["console"],
#         "level": "ERROR",  # Change to 'DEBUG' to see more detailed logs
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": "ERROR",  # Change to 'DEBUG' to see more detailed logs
#             "propagate": True,
#         },
#     },
# }
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # "standard": {"format": "%(levelname)s %(name)s %(message)s"},
        "colored": {
            "()": "config.settings.ColoredFormatter",
            # "format": "%(message)s",
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


EMAIL_HOST = 'mail-relay.lan.fyi'
EMAIL_PORT = 587
# EMAIL_USE_TLS = True

# EMAIL_HOST_USER = 'no-reply@dbca.wa.gov.au'
# EMAIL_HOST_PASSWORD = ''
# EMAIL_USE_SSL = False

ENVELOPE_EMAIL_RECIPIENTS = ['jarid.prince@dbca.wa.gov.au']
ENVELOPE_USE_HTML_EMAIL = True
# DEFAULT_FROM_EMAIL = '"SPMS" <SPMS-noreply@dbca.wa.gov.au>'
DEFAULT_FROM_EMAIL = '"SPMS" <spms-noreply@dbca.wa.gov.au>'



if DEBUG == True:
    SITE_URL = "127.0.0.1:3000"
else:
    SITE_URL = "https://scienceprojects-test.dbca.wa.gov.au"

