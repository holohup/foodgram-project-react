import os
from distutils.util import strtobool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY', 'p&l%385148kslhtyn^##a1)ilz@4zqj=rq&agdol^##zgl9(vs'
)

DEBUG = strtobool(os.getenv('DJANGO_DEBUG_MODE', 'False'))

ALLOWED_HOSTS = ['*', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users.apps.UsersConfig',
    'recipes.apps.RecipesConfig',
    'api.apps.ApiConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'djoser',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'foodgram.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('PGUSER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

STATIC_URL = '/static/django/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/django')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication'
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.PageLimitPagination',
    'PAGE_SIZE': 5,
    'SEARCH_PARAM': 'name',
}

DJOSER = {
    'LOGIN_FIELD': 'email',
    'HIDE_USERS': False,
    'PERMISSIONS': {
        'user_list': ['rest_framework.permissions.AllowAny'],
        'user': ['api.permissions.ReadOnly'],
    },
    'SERIALIZERS': {
        'user': 'api.serializers.CustomUserSubscriptionsSerializer',
        'user_create': 'api.serializers.CustomUserSerializer',
        'current_user': 'api.serializers.CustomUserSubscriptionsSerializer',
    },
}

CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://127.0.0.1', '*']
# CORS_ALLOWED_ORIGINS = [*]
# CORS_ALLOW_METHODS = (
#         'GET',
#         'POST',
#         'PUT',
#         'PATCH',
#         'DELETE',
#         'OPTIONS'
#     )
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'formatters': {
#         'formatter': {
#             '()': 'django.utils.log.ServerFormatter',
#             'format': '[%(name)s %(asctime)s %(filename)s: %(lineno)d - %(funcName)s()] %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S',
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'formatter',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ('console',),
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'django.db.backends': {
#             'handlers': ('console',),
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     },
# }
DEFAULT_RECIPES_LIMIT = 5
FAVORITED_CACHE_SECONDS_TTL = 60

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'foodgram-localmemcache',
    }
}

HOST_URL = 'http://' + ALLOWED_HOSTS[1]