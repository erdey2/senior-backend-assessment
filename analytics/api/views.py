from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from ..models import Blog, BlogView, Country
from .serializers import BlogViewsAnalyticsSerializer, TopAnalyticsSerializer
from datetime import datetime, timedelta

class BlogViewsAnalyticsAPIView(APIView):
    """
    GET /analytics/blog-views/?object_type=country&range=month
    """
    def get(self, request):
        object_type = request.GET.get('object_type', 'country')  # country/user
        time_range = request.GET.get('range', 'month')          # day/week/month/year

        blogs = Blog.objects.all()

        # Apply time range filter
        now = datetime.now()
        if time_range == 'month':
            start_date = now - timedelta(days=30)
        elif time_range == 'week':
            start_date = now - timedelta(days=7)
        elif time_range == 'year':
            start_date = now - timedelta(days=365)
        else:  # default: all time
            start_date = None

        if start_date:
            blogs = blogs.filter(created_at__gte=start_date)

        # Grouping
        if object_type == 'country':
            data = blogs.values('country__name').annotate(
                y=Count('id'),
                z=Sum('views__id')
            )
            for item in data:
                item['x'] = item.pop('country__name') or 'Unknown'
        else:  # group by user
            data = blogs.values('author__username').annotate(
                y=Count('id'),
                z=Sum('views__id')
            )
            for item in data:
                item['x'] = item.pop('author__username') or 'Unknown'

        # Serialize and return
        serializer = BlogViewsAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TopAnalyticsAPIView(APIView):

    def get(self, request):
        top_type = request.GET.get("top")
        time_range = request.GET.get("range", "month")

        if top_type not in ["user", "country", "blog"]:
            return Response(
                {"detail": "Invalid `top` parameter. Use user/country/blog."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter by time range
        now = datetime.now()

        if time_range == "week":
            start_date = now - timedelta(days=7)
        elif time_range == "month":
            start_date = now - timedelta(days=30)
        elif time_range == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = None

        blog_views = BlogView.objects.all()

        if start_date:
            blog_views = blog_views.filter(viewed_at__gte=start_date)

        # --- TOP BY USER ---
        if top_type == "user":
            data = (
                blog_views.values("blog__author__username")
                .annotate(
                    y=Count("blog", distinct=True),  # number of blogs
                    z=Count("id"),                   # total views
                )
                .order_by("-z")[:10]
            )
            for item in data:
                item["x"] = item.pop("blog__author__username") or "Unknown"

        # --- TOP BY COUNTRY ---
        elif top_type == "country":
            data = (
                blog_views.values("viewer_country__name")
                .annotate(
                    y=Count("blog", distinct=True),
                    z=Count("id"),
                )
                .order_by("-z")[:10]
            )
            for item in data:
                item["x"] = item.pop("viewer_country__name") or "Unknown"

        # --- TOP BY BLOG ---
        else:  # top_type == "blog"
            data = (
                blog_views.values("blog__title")
                .annotate(
                    y=1,            # for blog mode y = always 1
                    z=Count("id"),  # total views
                )
                .order_by("-z")[:10]
            )
            for item in data:
                item["x"] = item.pop("blog__title") or "Unknown"

        serializer = TopAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

