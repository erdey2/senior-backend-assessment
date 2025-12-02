from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, F, Window
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from ..models import BlogView
from .serializers import (
    BlogViewsAnalyticsSerializer,
    TopAnalyticsSerializer,
    PerformanceAnalyticsSerializer,
)
from .filters import BlogViewFilter  # We'll create this with django-filter


@extend_schema_view(
    blog_views=extend_schema(
        tags=["Analytics"],
        summary="Blog views grouped by viewer country or viewer user",
        parameters=[
            OpenApiParameter(name='object_type', type=str, enum=['country', 'user'], default='country'),
            OpenApiParameter(name='range', type=str, enum=['day', 'week', 'month', 'year']),
        ],
        responses=BlogViewsAnalyticsSerializer(many=True)
    ),
    top=extend_schema(
        tags=["Analytics"],
        summary="Top 10 viewers by country, user or blogs viewed",
        parameters=[
            OpenApiParameter(name='top', type=str, enum=['user', 'country', 'blog'], default='user'),
            OpenApiParameter(name='range', type=str, enum=['day', 'week', 'month', 'year']),
        ],
        responses=TopAnalyticsSerializer(many=True)
    ),
    performance=extend_schema(
        tags=["Analytics"],
        summary="Performance trend with growth % (calculated in DB)",
        parameters=[
            OpenApiParameter(name='compare', type=str, enum=['day', 'week', 'month', 'year'], default='month'),
            OpenApiParameter(name='user', type=int, description="Filter by blog author ID"),
        ],
        responses=PerformanceAnalyticsSerializer(many=True)
    ),
)
class AnalyticsViewSet(viewsets.ViewSet):
    # Proper time range filtering
    def _apply_time_range(self, queryset, time_range):
        now = timezone.now()
        ranges = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }
        delta = ranges.get(time_range)
        if delta:
            return queryset.filter(viewed_at__gte=now - delta)
        return queryset

    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        object_type = request.query_params.get('object_type', 'country')
        time_range = request.query_params.get('range', 'month')

        qs = BlogView.objects.filter(blog__isnull=False)

        # Use proper django-filter (see below)
        qs = BlogViewFilter(request.query_params, queryset=qs).qs
        qs = self._apply_time_range(qs, time_range)

        if object_type == "country":
            qs = qs.values(name=F("viewer_country__name")) \
                .annotate(
                    unique_blogs=Count("blog", distinct=True),
                    total_views=Count("id")
                )
        elif object_type == "user":
            qs = qs.exclude(user__isnull=True) \
                .values(name=F("user__username")) \
                .annotate(
                    unique_blogs=Count("blog", distinct=True),
                    total_views=Count("id")
                )
        else:
            return Response({"error": "Invalid object_type. Use 'country' or 'user'"}, status=400)

        serializer = BlogViewsAnalyticsSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        top_type = request.query_params.get('top', 'user')
        time_range = request.query_params.get('range', 'month')

        qs = BlogView.objects.filter(blog__isnull=False)
        qs = BlogViewFilter(request.query_params, queryset=qs).qs
        qs = self._apply_time_range(qs, time_range)

        if top_type == "user":
            qs = qs.exclude(user__isnull=True) \
                .values(name=F("user__username")) \
                .annotate(total_views=Count("id")) \
                .order_by("-total_views")[:10]
        elif top_type == "country":
            qs = qs.values(name=F("viewer_country__name")) \
                .annotate(total_views=Count("id")) \
                .order_by("-total_views")[:10]
        elif top_type == "blog":
            qs = qs.values(name=F("blog__title")) \
                .annotate(total_views=Count("id")) \
                .order_by("-total_views")[:10]
        else:
            return Response({"error": "Invalid top type"}, status=400)

        serializer = TopAnalyticsSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="performance")
    def performance(self, request):
        compare = request.query_params.get("compare", "month")
        user_id = request.query_params.get("user")

        qs = BlogView.objects.filter(blog__isnull=False)
        if user_id:
            qs = qs.filter(blog__author_id=user_id)

        qs = BlogViewFilter(request.query_params, queryset=qs).qs

        trunc_map = {
            "day": TruncDay("viewed_at"),
            "week": TruncWeek("viewed_at"),
            "month": TruncMonth("viewed_at"),
            "year": TruncYear("viewed_at"),
        }
        trunc = trunc_map.get(compare, TruncMonth("viewed_at"))

        annotated = qs.annotate(period=trunc) \
            .values("period") \
            .annotate(
                views=Count("id"),
                unique_blogs=Count("blog", distinct=True),
                prev_views=Window(
                    Lag("views", default=0),
                    order_by=F("period").asc()
                )
            ).values("period", "views", "unique_blogs", "prev_views") \
            .order_by("period")

        results = []
        for item in annotated:
            current = item["views"]
            prev = item["prev_views"]
            growth = round(((current - prev) / prev * 100), 2) if prev > 0 else None

            results.append({
                "x": item["period"].strftime('%Y-%m-%d'),
                "y": current,
                "z": growth,
                "blogs_count": item["unique_blogs"]
            })

        return Response(PerformanceAnalyticsSerializer(results, many=True).data)