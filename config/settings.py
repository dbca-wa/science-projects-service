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

DEBUG = False if env("DEBUG") == "False" else True
SECRET_KEY = env("SECRET_KEY")
EXTERNAL_PASS = env("EXTERNAL_PASS")
CF_IMAGES_TOKEN = env("CF_IMAGES_TOKEN")
CF_ACCOUNT_ID = env("CF_ACCOUNT_ID")
CF_UPLOAD_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/images/v2/direct_upload"

if env("DEBUG") == "True":
    INSTANCE_URL = "http://127.0.0.1:8000/"
else:
    if 'RENDER' not in os.environ:
        INSTANCE_URL = "https://scienceprojects-test-api.dbca.wa.gov.au"
    else:
        INSTANCE_URL = "https://idabblewith.xyz"

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

# Application definition

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

# DEBUG = "RENDER" not in os.environ  # Debug if not hosted on RENDER
# APPEND_SLASH = False

ROOT_URLCONF = "config.urls"
STATIC_URL = "/static/"
if not DEBUG:  # Whitenoise brotli config for static files on render
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

MEDIA_ROOT = "uploads"
MEDIA_URL = "user-uploads/"

PAGE_SIZE = 10
USER_LIST_PAGE_SIZE = 250


if not DEBUG:
    if 'RENDER' in os.environ:
        DATABASES = {
            "default": dj_database_url.config(
                conn_max_age=600,
            )
        }

    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": env("PRODUCTION_DB_NAME"),
                "USER": env("PRODUCTION_USERNAME"),
                "PASSWORD": env("PRODUCTION_PASSWORD"),
                "HOST": env(
                    "PRODUCTION_HOST"
                ),  # Use "db" as the hostname to refer to the PostgreSQL service
                "PORT": "5432",  # Use the PostgreSQL default port
                "OPTIONS": {
                    "options": "-c client_encoding=utf8",
                },
                "CONN_MAX_AGE": 600,
            }
        }
else:
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

        # "HOST": f"{env('HOST')}",
        # "PORT": f"{env('PORT')}",
ALLOWED_HOSTS = [
    # '*'
    # "scienceprojects-test-api.dbca.wa.gov.au",
    # "scienceprojects-test.dbca.wa.gov.au",
    # "cycle-test-clusterip.cycle",
    # "127.0.0.1",
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'X-CSRFToken',
    'Content-Type',
    # Add any other headers you need here
]
CORS_ALLOWED_ORIGINS = [
    "http://*",
    "https://*",
            # "https://scienceprojects-test.dbca.wa.gov.au",
    # "https://scienceprojects-test.dbca.wa.gov.au",
    # "https://scienceprojects-test-api.dbca.wa.gov.au",
    # "http://scienceprojects-test-api.dbca.wa.gov.au",
    # "http://scienceprojects-test.dbca.wa.gov.au",
    # "http://cycle-test-clusterip.cycle",
    # "http://cycle-test-clusterip.cycle:3000",
    # "http://127.0.0.1",
    # "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://*",
    "https://*",
            # "https://scienceprojects-test.dbca.wa.gov.au",
    # "https://scienceprojects-test-api.dbca.wa.gov.au",
    # "http://scienceprojects-test.dbca.wa.gov.au",
    # "http://scienceprojects-test-api.dbca.wa.gov.au",
    # "http://cycle-test-clusterip.cycle",
    # "http://cycle-test-clusterip.cycle:3000",
    # "http://127.0.0.1",
    # "http://127.0.0.1:3000",
]

CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
CORS_ALLOW_CREDENTIALS = True


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # "dbca_utils.middleware.SSOLoginMiddleware",
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

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManigestStaticFilesStorage"