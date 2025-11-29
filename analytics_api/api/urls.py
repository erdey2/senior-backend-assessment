from django.urls import path
from .views import BlogViewsAnalyticsAPIView

urlpatterns = [
    path('blog-views/', BlogViewsAnalyticsAPIView.as_view(), name='blog-views-analytics'),
]
