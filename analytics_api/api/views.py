from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from ..models import Blog, BlogView, Country
from .serializers import BlogViewsAnalyticsSerializer
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
