# region Imports ===============================================================================
import logging, os, sentry_sdk, dj_database_url, environ
from logging import LogRecord
from pathlib import Path

# endregion ========================================================================================

# region Project ENV ===================================================================
env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent
env.read_env(
    os.path.join(BASE_DIR, ".env"), overwrite=True
)  # Env takes precedence over shell / pc configured vars

# Environ detection
ENVIRONMENT = env("ENVIRONMENT", default="development")
DEBUG = ENVIRONMENT == "development"

# Core settings
SECRET_KEY = env("SECRET_KEY")
DATABASE_URL = env("DATABASE_URL")

# API configurations
EXTERNAL_PASS = env("EXTERNAL_PASS")
LIBRARY_API_URL = env("LIBRARY_API_URL")
LIBRARY_BEARER_TOKEN = env("LIBRARY_BEARER_TOKEN")
IT_ASSETS_ACCESS_TOKEN = env("IT_ASSETS_ACCESS_TOKEN")
IT_ASSETS_USER = env("IT_ASSETS_USER")
IT_ASSETS_URLS = {
    "production": "https://itassets.dbca.wa.gov.au/api/v3/departmentuser/",
    "staging": "https://itassets-uat.dbca.wa.gov.au/api/v3/departmentuser/",
    "development": "https://itassets-uat.dbca.wa.gov.au/api/v3/departmentuser/",
}
IT_ASSETS_URL = IT_ASSETS_URLS[ENVIRONMENT]

# Domain configuration
DOMAINS = {
    "production": {
        "main": "scienceprojects.dbca.wa.gov.au",
        "profiles": "science-profiles.dbca.wa.gov.au",
    },
    "staging": {
        "main": "scienceprojects-test.dbca.wa.gov.au",
        "profiles": "science-profiles-test.dbca.wa.gov.au",
    },
    "development": {
        "main": "127.0.0.1:3000",
        "profiles": "127.0.0.1:3000/staff",
    },
}

CURRENT_DOMAINS = DOMAINS[ENVIRONMENT]

# Site URL configuration
if DEBUG:
    SITE_URL = CURRENT_DOMAINS["main"]
    INSTANCE_URL = "http://127.0.0.1:8000/"
else:
    SITE_URL = f"https://{CURRENT_DOMAINS['main']}"
    INSTANCE_URL = SITE_URL


SITE_URL_HTTP = SITE_URL if DEBUG else f"https://{CURRENT_DOMAINS['main']}"

# Prince server configuration
PRINCE_SERVER_URL = env("PRINCE_SERVER_URL", default="")
if not DEBUG and not PRINCE_SERVER_URL:
    PRINCE_SERVER_URL = str(BASE_DIR)
# /usr/src/app/backend (for getting images using PrinceXML in container)

# App configuration
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500
PAGE_SIZE = 24
USER_LIST_PAGE_SIZE = 250
FILE_UPLOAD_PERMISSIONS = None  # Use default operating system file permissions

# URL Configuration - No trailing slashes (REST API best practice)
APPEND_SLASH = False

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
EMAIL_HOST = env("EMAIL_HOST", default="mail-relay.lan.fyi")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
ENVELOPE_EMAIL_RECIPIENTS = [env("SPMS_MAINTAINER_EMAIL")]
ENVELOPE_USE_HTML_EMAIL = True

# endregion ========================================================================================

# region Database =============================================================
DATABASES = {"default": dj_database_url.config()}

# Prod database optimisations
if not DEBUG:
    DATABASES["default"].update(
        {
            "CONN_MAX_AGE": 60,  # Connection pooling
            "OPTIONS": {
                "connect_timeout": 30,
                # "read_timeout": 60, # Invalid in this version
                # "write_timeout": 60, # Invalid in this version
            },
        }
    )

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

# region CORS, CSRF and Hosts =========================================================

# Get unique domains
if DEBUG:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "127.0.0.1:3000", "127.0.0.1:8000"]
else:
    ALLOWED_HOSTS = list(set(CURRENT_DOMAINS.values()))

# Remove duplicates
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))

# CSRF trusted origins
if DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1",
    ]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in CURRENT_DOMAINS.values()]

CSRF_COOKIE_NAME = "spmscsrf"  # Set custom CSRF cookie name

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

if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://127\.0\.0\.1:3000$",
    ]
# else: # handled by nginx
#     if not hasattr(globals(), "_CORS_CONFIGURED"):
#         CORS_ALLOWED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]
#         print(f"DEBUG: CORS_ALLOWED_ORIGINS = {CORS_ALLOWED_ORIGINS}")
#         globals()["_CORS_CONFIGURED"] = True


if not DEBUG:
    # Secure cookie configuration for production
    SESSION_COOKIE_DOMAIN = ".dbca.wa.gov.au"
    CSRF_COOKIE_DOMAIN = ".dbca.wa.gov.au"

    # Cross-site settings for multi-domain setup
    CSRF_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SAMESITE = "None"

    # Security settings
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

    # Additional security headers (handled by Nginx)
    # SECURE_SSL_REDIRECT = True
    # SECURE_HSTS_SECONDS = 31536000  # 1 year
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"

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
    "caretakers.apps.CaretakersConfig",
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
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # General API rate limits
        "anon": "200/hour",  # Anonymous users (login page, public endpoints)
        "user": "1000/hour",  # Authenticated users (normal usage)
        # Specific endpoint rate limits (use custom throttle classes)
        "burst": "30/minute",  # Burst protection for rapid requests
        "login": "5/minute",  # Login attempts (prevents brute force)
        "password_reset": "3/hour",  # Password reset requests
    },
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
if ENVIRONMENT != "development":
    sentry_sdk.init(
        environment=ENVIRONMENT,
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

# endregion ========================================================================================
