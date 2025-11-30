from .base import *
import os
import dj_database_url

# Production overrides
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["your-app-name.onrender.com"]

# Production database on neon
DATABASES = {
    'default': dj_database_url.parse(os.getenv("DATABASE_URL"))
}
