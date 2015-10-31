"""
Django settings for senso_api project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*3nn3vruj+&o+h&(0vcnk=33aiglj&%qy%ztu#-rz17vljlj%w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['10.2.64.115']


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'senso_api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'senso_api.urls'

WSGI_APPLICATION = 'senso_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'digital_env',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
    },
    'slave': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'digital_env',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Singapore'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'standard': {
            'format': '%(asctime)s|%(levelname)s|%(process)d:%(thread)d|%(filename)s:%(lineno)d|%(module)s.%(funcName)s|%(message)s',
        },
        'short' : {
            'format': '%(asctime)s|%(levelname)s|%(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/senso/main.log.%s' % (datetime.datetime.now().date(),),
            'formatter':'standard',
        },
        'file_sync': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/senso/sync.log.%s' % (datetime.datetime.now().date(),),
            'formatter':'standard',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'sync': {
            'handlers': ['file_sync'],
            'level': 'INFO',
            'propagate': True,
        },

    },
}

UPDATE_FREQUENCY = 300
ALERT_LIMIT = 1

SMS_SERVICE_HOST = 'sms.garenanow.com'
SMS_SERVICE_PORT = 8600
SMS_PREFIX=''
SMS_SOURCE='Cyberpay'
SENT_SMS = False
ALERT_NUMBER = 6581575586
