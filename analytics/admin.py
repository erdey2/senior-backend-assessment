from django.contrib import admin
from .models import Country, Blog, BlogView

admin.site.register(Country)
admin.site.register(Blog)
admin.site.register(BlogView)
