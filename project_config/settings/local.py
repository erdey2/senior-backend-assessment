from .base import *

# Development overrides
DEBUG = True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
