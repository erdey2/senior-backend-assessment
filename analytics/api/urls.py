from django.urls import path
from .views import BlogViewsAnalyticsAPIView, TopAnalyticsAPIView

urlpatterns = [
    path('blog-views/', BlogViewsAnalyticsAPIView.as_view(), name='blog-views-analytics'),
    path('top/', TopAnalyticsAPIView.as_view(), name='top-analytics'),
]
