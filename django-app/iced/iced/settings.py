"""
Django settings for iced project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from os.path import abspath, dirname, join  # noqa F401
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(join(dirname(__file__), "..", ".."))
APP_DIR = os.path.abspath(join(ROOT_DIR, "iced"))

dotenv_path = join(ROOT_DIR, ".env")
load_dotenv(dotenv_path)

# Check for DJANGO_DEVELOPMENT env variable
app_mode = os.environ.get("APP_MODE", "dev")
USE_DEV = app_mode == "dev"
# Check for docker usage to change DB URL (for migration commands etc.)
USE_DOCKER = bool(os.environ.get("DJANGO_DOCKER", False)) if USE_DEV else False
# Get hostname of app to add to allowed_hosts list
HOSTNAME = os.environ.get("APP_HOSTNAME", "hostname_not_set")
# Base URL used to access
BASE_URL = os.environ.get("BASE_URL", None)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Log Directory for logs
LOG_DIR = Path.joinpath(BASE_DIR.parent.parent, 'logs')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET", "insecure-098f3j02ibyus08vhbn")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = USE_DEV

# Google map key
GOOGLE_MAP_API_KEY = os.environ.get("GOOGLE_MAP_API_KEY", "NoGoogleMapKeySet")

ALLOWED_HOSTS = ["localhost", HOSTNAME]


# Application definition

INSTALLED_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "base.apps.CoreConfig",
    "api.apps.ApiConfig",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "import_export",
    "guardian",
    'django_crontab',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

# CSP Settings
# default source as self
CSP_DEFAULT_SRC = ("'self'", "*.googleapis.com")

# style from our domain and bootstrapcdn
CSP_STYLE_SRC = ("'self'", "unpkg.com", "'unsafe-inline'", "*.googleapis.com")

# scripts from our domain and other domains
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "*.googleapis.com",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "dmc.ice-d.org",
    "cdn.bokeh.org",
)

# images from our domain and other domains
CSP_IMG_SRC = ("'self'", "data:", "*.gstatic.com", "*.googleapis.com", "*.ice-d.org")


# loading manifest, workers, frames, etc
CSP_FONT_SRC = ("'self'", "*.googleapis.com", "*.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "*.googleapis.com")
CSP_OBJECT_SRC = ("'self'", "*.googleapis.com")
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_INCLUDE_NONCE_IN = ("script-src",)
CSP_MANIFEST_SRC = ("'self'",)
CSP_WORKER_SRC = ("'self'",)
CSP_MEDIA_SRC = ("'self'",)

ROOT_URLCONF = "iced.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "iced.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
import dj_database_url  # noqa

DATABASES = {"default": dj_database_url.config()}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static/base"),)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Override production variables if DJANGO_DEVELOPMENT env variable is set
if USE_DEV:
    from .settings_dev import *  # noqa: F403, F401
if USE_DOCKER:
    from .settings_docker import *  # noqa: F403, F401

# Additional override for use in GB dev environment
# This undoes part of settings_dev and returns DB location definition to
# .env file, so GB's dev environment is not in the repo
if os.environ.get("GB_DEV") == "yes":
    DATABASES = {"default": dj_database_url.config()}


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

SITE_ID = int(os.environ.get("SITE_ID", 0))

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/base/admin/login/"


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ]
}

CRONJOBS = [
    ('1 0 * * *', 'django.core.management.call_command', ['calculate_ages_v3']),
    ('1 1 * * *', 'django.core.management.call_command', ['calculate_ages_cl36']),
]

CSRF_TRUSTED_ORIGINS=['https://*.ice-d.org']
