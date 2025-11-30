from .base import *
from decouple import config
import dj_database_url

# Production overrides
DEBUG = False
ALLOWED_HOSTS = ['blog-analysis.onrender.com']

# Production database (Neon)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),  # Neon connection string
        conn_max_age=600,
        ssl_require=True
    )
}

