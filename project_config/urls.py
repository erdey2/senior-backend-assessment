from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API routes
    path("analytics/", include("analytics.api.urls")),
]

