from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from ..models import Blog, BlogView
from .serializers import PerformanceAnalyticsSerializer, BlogViewsAnalyticsSerializer, TopAnalyticsSerializer
from .filters import apply_filters


class AnalyticsViewSet(viewsets.ViewSet):

    def _apply_time_range(self, queryset, time_range):
        now = datetime.now()
        start_date = None
        if time_range == 'day':
            start_date = now - timedelta(days=1)
        elif time_range == 'week':
            start_date = now - timedelta(days=7)
        elif time_range == 'month':
            start_date = now - timedelta(days=30)
        elif time_range == 'year':
            start_date = now - timedelta(days=365)
        if start_date:
            return queryset.filter(viewed_at__gte=start_date)
        return queryset

    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        """
        object_type = country/user
        x = grouping key, y = number_of_blogs, z = total views
        """
        object_type = request.GET.get('object_type', 'country')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        blogs = Blog.objects.select_related('author', 'country').prefetch_related('views')

        if filters:
            blogs = apply_filters(blogs, filters)

        blogs = self._apply_time_range(blogs, time_range)

        if object_type == 'country':
            qs = blogs.values('country__name').annotate(
                y=Count('id'),
                z=Count('views')
            )
            data = [{"x": b["country__name"] or "Unknown", "y": b["y"], "z": b["z"]} for b in qs]
        else:
            qs = blogs.values('author__username').annotate(
                y=Count('id'),
                z=Count('views')
            )
            data = [{"x": b["author__username"] or "Unknown", "y": b["y"], "z": b["z"]} for b in qs]

        serializer = BlogViewsAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        """
        Returns Top 10 based on total views
        """
        top_type = request.GET.get('top', 'user')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        blogs = Blog.objects.select_related('author', 'country').prefetch_related('views')

        if filters:
            blogs = apply_filters(blogs, filters)

        blogs = self._apply_time_range(blogs, time_range)

        if top_type == 'user':
            qs = blogs.values('author__username').annotate(
                y=Count('id'),
                z=Count('views')
            ).order_by('-z')[:10]
            data = [{"x": b['author__username'], "y": b['y'], "z": b['z']} for b in qs]

        elif top_type == 'country':
            qs = blogs.values('country__name').annotate(
                y=Count('id'),
                z=Count('views')
            ).order_by('-z')[:10]
            data = [{"x": b['country__name'] or "Unknown", "y": b['y'], "z": b['z']} for b in qs]

        else:  # top blogs
            qs = blogs.annotate(
                y=1,  # each blog counts as 1
                z=Count('views')
            ).order_by('-z')[:10]
            data = [{"x": b.title, "y": b.y, "z": b.z} for b in qs]

        serializer = TopAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="performance")
    def performance(self, request):
        """
        x = period label
        y = total views
        z = growth/decline % vs previous period
        """

        compare = request.GET.get("compare", "month")  # day, week, month, year
        user_id = request.GET.get("user", None)
        filters = request.GET.get("filters", None)

        # Base queryset
        qs = BlogView.objects.select_related("blog", "blog__author")

        if user_id:
            qs = qs.filter(blog__author_id=user_id)

        if filters:
            qs = apply_filters(qs, filters)

        # trunc function
        if compare == "day":
            trunc = TruncDay("viewed_at")
            label_format = "%Y-%m-%d"
        elif compare == "week":
            trunc = TruncWeek("viewed_at")
            label_format = "Week %U %Y"
        elif compare == "year":
            trunc = TruncYear("viewed_at")
            label_format = "%Y"
        else:  # month as default
            trunc = TruncMonth("viewed_at")
            label_format = "%B %Y"

        # Single-query total views per period
        period_data = (
            qs.annotate(period=trunc)
            .values("period")
            .annotate(
                views_count=Count("id"),
                blogs_count=Count("blog", distinct=True),
            )
            .order_by("period")
        )

        # Convert to dict
        period_map = {
            item["period"]: {
                "views": item["views_count"],
                "blogs": item["blogs_count"],
            }
            for item in period_data
        }

        # Build final dataset with growth %
        periods = list(period_map.keys())
        periods.sort()

        output = []
        for i, period in enumerate(periods):
            current = period_map[period]

            # previous period lookup
            prev_views = (
                period_map.get(periods[i - 1], {}).get("views", 0)
                if i > 0 else 0
            )

            # growth %
            if prev_views > 0:
                growth = ((current["views"] - prev_views) / prev_views) * 100
            else:
                growth = 100.0  # assume 100% when starting

            output.append({
                "x": period.strftime(label_format) + f" ({current['blogs']} blogs)",
                "y": current["views"],
                "z": round(growth, 2),
            })

        serializer = PerformanceAnalyticsSerializer(output, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

