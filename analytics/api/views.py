from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Blog, BlogView
from .serializers import PerformanceAnalyticsSerializer, BlogViewsAnalyticsSerializer, TopAnalyticsSerializer
from .filters import apply_filters


class AnalyticsViewSet(viewsets.ViewSet):

    def _apply_time_range(self, queryset, time_range):
        now = timezone.now()
        if time_range == "day":
            start = now - timedelta(days=1)
        elif time_range == "week":
            start = now - timedelta(days=7)
        elif time_range == "month":
            start = now - timedelta(days=30)
        elif time_range == "year":
            start = now - timedelta(days=365)
        else:
            return queryset

        return queryset.filter(viewed_at__gte=start)

    # BLOG-VIEWS API
    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        """
        - object_type = country / user
        - x = grouping key
        - y = number_of_blogs
        - z = total_views
        """
        object_type = request.GET.get('object_type', 'country')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        # Base queryset
        qs = BlogView.objects.select_related( "blog", "blog__author", "blog__country")

        # Apply dynamic filters
        if filters:
            qs = apply_filters(qs, filters)

        # Apply time range
        qs = self._apply_time_range(qs, time_range)

        # GROUPING
        if object_type == "country":
            qs = qs.values("blog__country__name").annotate(
                number_of_blogs=Count("blog", distinct=True),
                total_views=Count("id")
            )
            data = [{
                "x": row["blog__country__name"] or "Unknown",
                "y": row["number_of_blogs"],
                "z": row["total_views"]
            } for row in qs]

        elif object_type == "user":
            qs = qs.values("blog__author__username").annotate(
                number_of_blogs=Count("blog", distinct=True),
                total_views=Count("id")
            )
            data = [{
                "x": row["blog__author__username"] or "Unknown",
                "y": row["number_of_blogs"],
                "z": row["total_views"]
            } for row in qs]

        else:
            return Response(
                {"error": "Invalid object_type. Use: country or user"},
                status=400
            )

        serializer = BlogViewsAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=200)

    # TOP ANALYTICS API
    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        """
        Returns Top 10 (user / country / blogs) based on total views.
        """
        top_type = request.GET.get('top', 'user')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        qs = BlogView.objects.select_related("blog", "blog__author", "blog__country")

        if filters:
            qs = apply_filters(qs, filters)

        qs = self._apply_time_range(qs, time_range)

        if top_type == 'user':
            data = [
                {"x": row["blog__author__username"], "y": row["blogs_count"], "z": row["views_count"]}
                for row in qs.values("blog__author__username")
                .annotate(
                    blogs_count=Count("blog", distinct=True),
                    views_count=Count("id")
                )
                .order_by("-views_count")[:10]
            ]

        elif top_type == 'country':
            data = [
                {"x": row["blog__country__name"] or "Unknown", "y": row["blogs_count"], "z": row["views_count"]}
                for row in qs.values("blog__country__name")
                .annotate(
                    blogs_count=Count("blog", distinct=True),
                    views_count=Count("id")
                )
                .order_by("-views_count")[:10]
            ]

        else:  # top blogs
            data = [
                {"x": row["blog__title"], "y": 1, "z": row["views_count"]}
                for row in qs.values("blog__title")
                .annotate(views_count=Count("id"))
                .order_by("-views_count")[:10]
            ]

        serializer = TopAnalyticsSerializer(data, many=True)
        return Response(serializer.data, status=200)

    # PERFORMANCE ANALYTICS API
    @action(detail=False, methods=["get"], url_path="performance")
    def performance(self, request):
        """
        x = period label
        y = total views
        z = growth percentage
        """
        compare = request.GET.get("compare", "month")  # day/week/month/year
        user_id = request.GET.get("user", None)
        filters = request.GET.get("filters", None)

        qs = BlogView.objects.select_related("blog", "blog__author")

        if user_id:
            qs = qs.filter(blog__author_id=user_id)

        if filters:
            qs = apply_filters(qs, filters)

        # Choose truncation
        if compare == "day":
            trunc = TruncDay("viewed_at")
            label_format = "%Y-%m-%d"
        elif compare == "week":
            trunc = TruncWeek("viewed_at")
            label_format = "Week %U %Y"
        elif compare == "year":
            trunc = TruncYear("viewed_at")
            label_format = "%Y"
        else:  # default month
            trunc = TruncMonth("viewed_at")
            label_format = "%B %Y"

        # Query views per period
        period_data = (
            qs.annotate(period=trunc)
            .values("period")
            .annotate(
                views_count=Count("id"),
                blogs_count=Count("blog", distinct=True),
            )
            .order_by("period")
        )

        # Build structured output
        periods = list(period_data)
        output = []

        for i, p in enumerate(periods):
            current_views = p["views_count"]
            prev_views = periods[i - 1]["views_count"] if i > 0 else 0

            if prev_views > 0:
                growth = ((current_views - prev_views) / prev_views) * 100
            else:
                growth = 100.0

            output.append({
                "x": p["period"].strftime(label_format) + f" ({p['blogs_count']} blogs)",
                "y": current_views,
                "z": round(growth, 2),
            })

        serializer = PerformanceAnalyticsSerializer(output, many=True)
        return Response(serializer.data, status=200)
