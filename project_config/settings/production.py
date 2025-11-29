from .base import *
from decouple import config, Csv

# Production overrides
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv)

# Production database should be configured via environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
    }
}
