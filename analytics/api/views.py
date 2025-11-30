from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import BlogView
from .serializers import PerformanceAnalyticsSerializer, BlogViewsAnalyticsSerializer, TopAnalyticsSerializer
from .filters import apply_filters


class AnalyticsViewSet(viewsets.ViewSet):

    def _apply_time_range(self, queryset, time_range):
        """
        Filters queryset based on a time range: day, week, month, year
        """
        now = timezone.now()
        delta_map = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }

        if time_range not in delta_map:
            return queryset  # ignore invalid ranges

        start = now - delta_map[time_range]
        return queryset.filter(viewed_at__gte=start)

    # BLOG-VIEWS API
    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        object_type = request.GET.get('object_type', 'country')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        qs = BlogView.objects.select_related("blog", "blog__author", "blog__country").filter(blog__isnull=False)

        if filters:
            qs = apply_filters(qs, filters)

        qs = self._apply_time_range(qs, time_range)

        if object_type == "country":
            qs = qs.filter(blog__country__isnull=False).values("blog__country__name").annotate(
                number_of_blogs=Count("blog", distinct=True),
                total_views=Count("id")
            )
            data = [
                {
                    "x": row.get("blog__country__name") or "Unknown",
                    "y": row["number_of_blogs"],
                    "z": row["total_views"]
                } for row in qs
            ]

        elif object_type == "user":
            qs = qs.filter(blog__author__isnull=False).values("blog__author__username").annotate(
                number_of_blogs=Count("blog", distinct=True),
                total_views=Count("id")
            )
            data = [
                {
                    "x": row.get("blog__author__username") or "Unknown",
                    "y": row["number_of_blogs"],
                    "z": row["total_views"]
                } for row in qs
            ]

        else:
            return Response({"error": "Invalid object_type. Use: country or user"}, status=400)

        serializer = BlogViewsAnalyticsSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    # TOP ANALYTICS API
    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        top_type = request.GET.get('top', 'user')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters", None)

        qs = BlogView.objects.select_related("blog", "blog__author", "blog__country").filter(blog__isnull=False)

        if filters:
            qs = apply_filters(qs, filters)

        qs = self._apply_time_range(qs, time_range)

        if top_type == 'user':
            qs = qs.filter(blog__author__isnull=False).values("blog__author__username").annotate(
                blogs_count=Count("blog", distinct=True),
                views_count=Count("id")
            ).order_by("-views_count")[:10]

            data = [
                {"x": row.get("blog__author__username") or "Unknown", "y": row["blogs_count"], "z": row["views_count"]}
                for row in qs
            ]

        elif top_type == 'country':
            qs = qs.filter(blog__country__isnull=False).values("blog__country__name").annotate(
                blogs_count=Count("blog", distinct=True),
                views_count=Count("id")
            ).order_by("-views_count")[:10]

            data = [
                {"x": row.get("blog__country__name") or "Unknown", "y": row["blogs_count"], "z": row["views_count"]}
                for row in qs
            ]

        else:  # top blogs
            qs = qs.values("blog__title").annotate(
                views_count=Count("id")
            ).order_by("-views_count")[:10]

            data = [
                {"x": row.get("blog__title") or "Unknown", "y": 1, "z": row["views_count"]}
                for row in qs
            ]

        serializer = TopAnalyticsSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    # PERFORMANCE ANALYTICS API
    @action(detail=False, methods=["get"], url_path="performance")
    def performance(self, request):
        compare = request.GET.get("compare", "month")
        user_id = request.GET.get("user")
        filters = request.GET.get("filters")

        qs = BlogView.objects.select_related("blog", "blog__author").filter(blog__isnull=False)
        if user_id:
            qs = qs.filter(blog__author_id=user_id)
        if filters:
            qs = apply_filters(qs, filters)

        trunc_map = {
            "day": (TruncDay("viewed_at"), "%Y-%m-%d"),
            "week": (TruncWeek("viewed_at"), "Week %U %Y"),
            "month": (TruncMonth("viewed_at"), "%B %Y"),
            "year": (TruncYear("viewed_at"), "%Y"),
        }
        trunc, label_format = trunc_map.get(compare, trunc_map["month"])

        period_data = (
            qs.annotate(period=trunc)
            .values("period")
            .annotate(
                views_count=Count("id"),
                blogs_count=Count("blog", distinct=True),
            )
            .order_by("period")
        )

        output = []
        periods = list(period_data)
        for i, p in enumerate(periods):
            current_views = p["views_count"]
            prev_views = periods[i - 1]["views_count"] if i > 0 else 0
            growth = ((current_views - prev_views) / prev_views * 100) if prev_views > 0 else 100.0
            output.append({
                "x": (p["period"].strftime(label_format) if p["period"] else "Unknown") + f" ({p['blogs_count']} blogs)",
                "y": current_views,
                "z": round(growth, 2),
            })

        serializer = PerformanceAnalyticsSerializer(data=output, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)