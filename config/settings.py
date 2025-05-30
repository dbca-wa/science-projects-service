# region Imports ===============================================================================
import logging, os, sentry_sdk, dj_database_url, environ
from logging import LogRecord
from pathlib import Path

# endregion ========================================================================================

# region Project ENV ===================================================================
env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
env.read_env(os.path.join(BASE_DIR, ".env"), overwrite=True)  # Add overwrite=True
# APPEND_SLASH=False
DEBUG = True if os.environ.get("DJANGO_DEBUG") != "False" else False
DATABASE_URL = os.environ.get("DATABASE_URL")
ON_TEST_NETWORK = True if os.environ.get("ON_TEST_NETWORK") != "False" else False
SITE_URL_HTTP = f'https://{env("SITE_URL")}'
SECRET_KEY = env("SECRET_KEY")
EXTERNAL_PASS = env("EXTERNAL_PASS")
LIBRARY_API_URL = env("LIBRARY_API_URL")
LIBRARY_BEARER_TOKEN = env("LIBRARY_BEARER_TOKEN")
IT_ASSETS_ACCESS_TOKEN = env("IT_ASSETS_ACCESS_TOKEN")
IT_ASSETS_USER = env("IT_ASSETS_USER")
IT_ASSETS_URL = "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/"
if DEBUG or ON_TEST_NETWORK:
    IT_ASSETS_URL = "https://itassets-uat.dbca.wa.gov.au/api/v3/departmentuser/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500  # For admin mass gen
PAGE_SIZE = 10
USER_LIST_PAGE_SIZE = 250

# Use default operating system file permissions
FILE_UPLOAD_PERMISSIONS = None

# endregion ========================================================================================

# region Internationalization ==========================================================
TIME_ZONE = "Australia/Perth"
LANGUAGE_CODE = "en-au"
USE_I18N = True
USE_TZ = True

# endregion ========================================================================================

# region Media, Roots and Storage =====================================================
ROOT_URLCONF = "config.urls"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/files/"
MEDIA_ROOT = os.path.join(BASE_DIR, "files")
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# endregion ========================================================================================

# region Email Config =========================================================
EMAIL_HOST = os.environ.get("EMAIL_HOST", "mail-relay.lan.fyi")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
ENVELOPE_EMAIL_RECIPIENTS = [env("SPMS_MAINTAINER_EMAIL")]
ENVELOPE_USE_HTML_EMAIL = True

# endregion ========================================================================================

# region Database =============================================================
DATABASES = {"default": dj_database_url.config()}

# endregion ========================================================================================

# region Auth =========================================================
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

# endregion ========================================================================================

# region CORS and Hosts =========================================================

# /usr/src/app/backend (for getting images using PrinceXML)
PRINCE_SERVER_URL = env("PRINCE_SERVER_URL")
if not DEBUG and PRINCE_SERVER_URL == "":
    PRINCE_SERVER_URL = BASE_DIR


if DEBUG:
    SITE_URL = "127.0.0.1:3000"
    INSTANCE_URL = "http://127.0.0.1:8000/"
else:
    SITE_URL = SITE_URL_HTTP
    INSTANCE_URL = SITE_URL_HTTP


ALLOW_LIST = [
    # prod
    "scienceprojects-test.dbca.wa.gov.au",
    "scienceprojects.dbca.wa.gov.au",
    "science-profiles-test.dbca.wa.gov.au",
    "science-profiles.dbca.wa.gov.au",
    "127.0.0.1:3000",
    "127.0.0.1",
]

if not DEBUG and not PRINCE_SERVER_URL.startswith("/usr"):
    ALLOW_LIST.append(PRINCE_SERVER_URL)

# Ensure ALLOW_LIST is unique
ALLOW_LIST = list(set(ALLOW_LIST))
ALLOWED_HOSTS = ALLOW_LIST

CSRF_TRUSTED_ORIGINS = [
    "https://scienceprojects-test.dbca.wa.gov.au",
    "https://scienceprojects.dbca.wa.gov.au",
    "https://science-profiles-test.dbca.wa.gov.au",
    "https://science-profiles.dbca.wa.gov.au",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
]

if DEBUG:
    # Ensure all dbca subroutes allowed and local dev
    CORS_ALLOWED_ORIGIN_REGEXES = [
        # r"^https://.*\.dbca\.wa\.gov\.au$", #duplicate policies
        r"^http://127\.0\.0\.1:3000$",
    ]

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
    "Authorization",
]

CSRF_COOKIE_NAME = "spmscsrf"  # Set custom CSRF cookie name

if not DEBUG:
    SESSION_COOKIE_DOMAIN = ".dbca.wa.gov.au"
    CSRF_COOKIE_DOMAIN = ".dbca.wa.gov.au"

    # Ensure SameSite attribute allows cross-site requests if needed
    CSRF_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SAMESITE = "None"
    # Secure attribute is also recommended if using HTTPS
    CSRF_COOKIE_SECURE = DEBUG == False
    SESSION_COOKIE_SECURE = DEBUG == False

# endregion ========================================================================================

# region Application definitions ======================================================
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

# endregion ========================================================================================

# region Logs and Tracking =======================================================================
if not DEBUG:
    env_type = (
        "production"
        if ON_TEST_NETWORK == False or ON_TEST_NETWORK == "False"
        else "staging"
    )

    def before_send(event, hint):
        # Filter out N+1 query errors by checking the message or tags
        if event.get("logentry") and "N+1" in event["logentry"].get("message", ""):
            return None
        return event

    sentry_sdk.init(
        environment=env_type,
        dsn=env("SENTRY_URL"),
        before_send=before_send,
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

# endregion ========================================================================================
