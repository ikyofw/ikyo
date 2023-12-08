"""
Django settings for ikyo project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import logging
import os
import threading
from pathlib import Path

from iktools import (TEMPLATE_FOLDER, IkConfig, getDjangoAppConfigs,
                     getStaticFolder)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure--v(0wb&!a4gzk_@+r&2i1xnnfq7nu4mb84wjr+itd%lki+kft)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not IkConfig.production

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django_extensions',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
]
INSTALLED_APPS.extend(getDjangoAppConfigs())

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.log.logMiddleware.RequestLogMiddleware',
    'core.core.requestMiddleware.IkRequestMiddleware',
]

# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']

ROOT_URLCONF = 'django_backend.urls'

__TEMPLATES_DIRS = [os.path.join(BASE_DIR, TEMPLATE_FOLDER)]
for dirItem in IkConfig.get('System', 'templateDirs').split(','):
    dirItem = dirItem.strip()
    if dirItem != '':
        if dirItem[0] == '/' or ':' in dirItem:  # Absolute path in Linux & Windows
            __TEMPLATES_DIRS.append(dirItem)
        elif dirItem != TEMPLATE_FOLDER:
            __TEMPLATES_DIRS.append(os.path.join(BASE_DIR, dirItem))
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': __TEMPLATES_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {}
databaseName = IkConfig.get('Database', 'name')
if not databaseName:
    databaseName = ''
databaseEngine = IkConfig.get('Database', 'engine')
if databaseEngine == 'django.db.backends.sqlite3':
    if not (databaseName.startswith('/') or ':' in databaseName):
        databaseName = BASE_DIR / 'db.sqlite3'
DATABASES = {
    'default': {
        'ENGINE': databaseEngine,
        'NAME': databaseName,
        'USER': IkConfig.get('Database', 'user'),
        "PASSWORD": IkConfig.get('Database', 'password'),
        "HOST": IkConfig.get('Database', 'host'),
        'PORT': int(IkConfig.get('Database', 'port')) if IkConfig.get('Database', 'port') else None,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    getStaticFolder()
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Reference to https://docs.djangoproject.com/en/4.2/topics/http/sessions/
SESSION_COOKIE_AGE = int(IkConfig.get('Session', 'timeout'))  # in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# rest_framework.authentication.TokenAuthentication

REST_FRAMEWORK = {
    # global authenticate class.
    "DEFAULT_PERMISSON_CLASSES":    ['backend.authentication.index.UserPermission'],
}


# Loggers:
# Reference to https://docs.djangoproject.com/en/4.2/topics/logging/
#              https://blog.csdn.net/tofu_yi/article/details/118566756
# Usage:
#   import logging
#   logger = logging.getLoger(__name__)
#   or
#   logger = logging.getLogger('loggerName')
local = threading.local()


class DjangoLogFilter(logging.Filter):

    def __init__(self, fields):
        self.fields = fields

    def filter(self, record):
        record.path = getattr(local, 'path', "none")
        record.username = getattr(local, 'username', "none")
        if record.funcName == 'debug_sql' and record.levelname == 'DEBUG':
            if 'ik_screen_field_widget' in record.sql:
                print(record.sql)
        return True


LOGS_DIR = os.path.join(BASE_DIR, 'var', 'logs')
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(username)s %(asctime)s %(threadName)s:%(thread)d task_id:%(name)s %(filename)s:%(lineno)d %(levelname)s %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s %(threadName)s:%(thread)d task_id:%(name)s %(filename)s:%(lineno)d %(levelname)s %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '%(username)s %(levelname)s %(asctime)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'django_filter': {
            '()': 'django_backend.settings.DjangoLogFilter',
            'fields': {
            },
        },
        'request_info': {'()': 'core.log.logMiddleware.RequestLogFilter'}
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['django_filter', 'request_info'],
        },
        'djangoFile': {
            'level': 'DEBUG',   # INFO
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 50,
            'delay': True,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'filters': ['django_filter'],
        },
        'ikFile': {
            'level': 'DEBUG',   # INFO
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django_backend.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 50,
            'delay': True,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'email': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'djangoFile'],
            'level': 'DEBUG' if IkConfig.isDebug else 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['ikFile'],
            'propagate': True,
            'level': 'DEBUG' if IkConfig.isDebug else 'INFO',
        },
        'ikyo': {
            'handlers': ['console', 'ikFile'],
            'level': 'DEBUG' if IkConfig.isDebug else 'INFO',
            'propagate': True,
        },
    },
}