from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, F, Value
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from ..models import BlogView
from .serializers import PerformanceAnalyticsSerializer, BlogViewsAnalyticsSerializer, TopAnalyticsSerializer
from .filters import apply_filters


@extend_schema_view(
    blog_views=extend_schema(
        tags=["Analytics"],
        summary="Blog views by country or user",
        description="Returns aggregated views grouped by country or user.",
        parameters=[
            OpenApiParameter(name='object_type', required=False, description='country or user'),
            OpenApiParameter(name='range', required=False, description='day | week | month | year'),
            OpenApiParameter(name='filters', required=False),
        ]
    ),
    top=extend_schema(
        tags=["Analytics"],
        summary="Top 10 analytics (users, countries, blogs)",
        parameters=[
            OpenApiParameter(name='top', required=False, description='user | country | blog'),
            OpenApiParameter(name='range', required=False),
            OpenApiParameter(name='filters', required=False),
        ]
    ),
    performance=extend_schema(
        tags=["Analytics"],
        summary="Performance analytics over time",
        parameters=[
            OpenApiParameter(name='compare', required=False, description='day | week | month | year'),
            OpenApiParameter(name='user', required=False),
            OpenApiParameter(name='filters', required=False),
        ]
    )
)
class AnalyticsViewSet(viewsets.ViewSet):

    def _apply_time_range(self, queryset, time_range):
        now = timezone.now()
        ranges = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }
        if time_range not in ranges:
            return queryset

        return queryset.filter(viewed_at__gte=now - ranges[time_range])


    # BLOG VIEWS ANALYTICS
    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        object_type = request.GET.get('object_type', 'country')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters")

        qs = BlogView.objects.select_related("blog", "blog__author", "blog__country").filter(blog__isnull=False)

        if filters:
            qs = apply_filters(qs, filters)

        qs = self._apply_time_range(qs, time_range)

        if object_type == "country":
            qs = qs.values(name=F("blog__country__name")).annotate(y=Count("blog", distinct=True), z=Count("id"))
        elif object_type == "user":
            qs = qs.values(name=F("blog__author__username")).annotate(y=Count("blog", distinct=True), z=Count("id"))
        else:
            return Response({"error": "Invalid object_type"}, status=400)

        serializer = BlogViewsAnalyticsSerializer(qs, many=True)
        return Response(serializer.data)


    # TOP 10 ANALYTICS
    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        top_type = request.GET.get('top', 'user')
        time_range = request.GET.get('range', 'month')
        filters = request.GET.get("filters")

        qs = BlogView.objects.select_related("blog", "blog__author", "blog__country").filter(blog__isnull=False)

        if filters:
            qs = apply_filters(qs, filters)

        qs = self._apply_time_range(qs, time_range)

        if top_type == "user":
            qs = qs.values(name=F("blog__author__username")).annotate(y=Count("blog", distinct=True), z=Count("id")).order_by("-z")[:10]

        elif top_type == "country":
            qs = qs.values(name=F("blog__country__name")).annotate(y=Count("blog", distinct=True), z=Count("id")).order_by("-z")[:10]

        else:  # top blogs
            qs = qs.values(name=F("blog__title")).annotate(y=Value(1), z=Count("id")).order_by("-z")[:10]

        serializer = TopAnalyticsSerializer(qs, many=True)
        return Response(serializer.data)


    # PERFORMANCE ANALYTICS
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
            "day": TruncDay("viewed_at"),
            "week": TruncWeek("viewed_at"),
            "month": TruncMonth("viewed_at"),
            "year": TruncYear("viewed_at"),
        }
        trunc = trunc_map.get(compare, TruncMonth("viewed_at"))

        periods = (
            qs.annotate(period=trunc)
              .values("period")
              .annotate(
                  y=Count("id"),
                  blogs_count=Count("blog", distinct=True),
              )
              .order_by("period")
        )

        # Calculate growth directly in Python (efficient since list is small)
        results = []
        prev = 0
        for p in periods:
            current = p["y"]
            growth = ((current - prev) / prev * 100) if prev > 0 else 100.0
            prev = current

            results.append({
                "x": f"{p['period'].strftime('%Y-%m-%d')} ({p['blogs_count']} blogs)",
                "y": current,
                "z": round(growth, 2),
            })

        serializer = PerformanceAnalyticsSerializer(results, many=True)
        return Response(serializer.data)
