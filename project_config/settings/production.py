from .base import *
import dj_database_url
from decouple import config

# Production overrides
DEBUG = False
ALLOWED_HOSTS = ['blog-analysis.onrender.com']

# Production database on neon
DATABASES = {
    'default': dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}
