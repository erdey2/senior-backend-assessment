from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, F, Value
from django.db.models.functions import Coalesce, TruncDay, TruncWeek, TruncMonth, TruncYear

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from ..models import BlogView
from .serializers import BlogViewsAnalyticsSerializer, TopAnalyticsSerializer, PerformanceAnalyticsSerializer
from .filters import BlogViewFilter


@extend_schema_view(
    blog_views=extend_schema(
        tags=["Analytics"],
        summary="Blog views grouped by viewer country or viewer user",
        description="Group by viewer country or viewer user. Returns list of {x, y, z}.",
        parameters=[
            OpenApiParameter(name='object_type', description="country | user", required=False, type=str, enum=['country','user'], default='country'),
            OpenApiParameter(name='range', description="day | week | month | year", required=False, type=str, enum=['day','week','month','year'], default='month'),
            OpenApiParameter(name='viewer_country', description="Filter by viewer country code (e.g. ET)", required=False),
            OpenApiParameter(name='blog_country', description="Filter by blog country code (e.g. ET)", required=False),
            OpenApiParameter(name='blog_author', description="Filter by blog author id", required=False),
            OpenApiParameter(name='user', description="Filter by viewer user id", required=False),
            OpenApiParameter(name='viewed_at_gte', description="ISO datetime lower bound", required=False),
            OpenApiParameter(name='viewed_at_lte', description="ISO datetime upper bound", required=False),
        ],
        responses=BlogViewsAnalyticsSerializer(many=True),
        examples=[
            OpenApiExample(
                "By country example",
                value=[{"x":"Ethiopia","y":12,"z":1200},{"x":"Kenya","y":5,"z":420}],
                response_only=True
            )
        ]
    ),
    top=extend_schema(
        tags=["Analytics"],
        summary="Top 10 by user / country / blog (by total views)",
        parameters=[
            OpenApiParameter(name='top', description="user | country | blog", required=False, type=str, enum=['user','country','blog'], default='user'),
            OpenApiParameter(name='range', description="day | week | month | year", required=False, type=str, enum=['day','week','month','year'], default='month'),
        ],
        responses=TopAnalyticsSerializer(many=True),
        examples=[
            OpenApiExample("Top users sample", value=[{"x":"alice","y":5,"z":520}], response_only=True)
        ]
    ),
    performance=extend_schema(
        tags=["Analytics"],
        summary="Performance trend per period with growth %",
        parameters=[
            OpenApiParameter(name='compare', description="day | week | month | year", required=False, type=str, enum=['day','week','month','year'], default='month'),
            OpenApiParameter(name='user', description="Filter by blog author id", required=False),
        ],
        responses=PerformanceAnalyticsSerializer(many=True),
        examples=[
            OpenApiExample("Monthly perf sample", value=[{"x":"2025-10-01 (5 blogs)","y":120,"z":10.0}], response_only=True)
        ]
    ),
)
class AnalyticsViewSet(viewsets.ViewSet):
    """
    Analytics endpoints:
    - /analytics/blog-views/?object_type=country&range=month
    - /analytics/top/?top=user&range=month
    - /analytics/performance/?compare=month&user=1
    """
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

    # blog-views
    @action(detail=False, methods=['get'], url_path='blog-views')
    def blog_views(self, request):
        object_type = request.query_params.get('object_type', 'country')
        time_range = request.query_params.get('range', 'month')

        qs = BlogView.objects.select_related(
            'blog', 'blog__author', 'blog__country', 'viewer_country', 'user'
        ).filter(blog__isnull=False)

        qs = BlogViewFilter(request.query_params, queryset=qs).qs
        qs = self._apply_time_range(qs, time_range)

        if object_type == 'country':
            data = qs.values(
                x=Coalesce(F('viewer_country__name'), Value('Unknown'))
            ).annotate(
                y=Count('blog', distinct=True),
                z=Count('id')
            ).order_by('-z').values('x', 'y', 'z')

        elif object_type == 'user':
            data = qs.exclude(user__isnull=True).values(
                x=F('user__username')
            ).annotate(
                y=Count('blog', distinct=True),
                z=Count('id')
            ).order_by('-z').values('x', 'y', 'z')

        else:
            return Response(
                {"error": "Invalid object_type. Use 'country' or 'user'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(list(data))

    # top views
    @action(detail=False, methods=['get'], url_path='top')
    def top(self, request):
        top_type = request.query_params.get('top', 'user')
        time_range = request.query_params.get('range', 'month')

        # Base queryset with necessary joins
        qs = BlogView.objects.select_related(
            'blog', 'blog__author', 'blog__country', 'viewer_country', 'user'
        ).filter(blog__isnull=False)

        # Apply filters + time range
        qs = BlogViewFilter(request.query_params, queryset=qs).qs
        qs = self._apply_time_range(qs, time_range)

        if top_type == 'user':
            data = (
                qs.exclude(user__isnull=True)
                .values(x=F('user__username'))
                .annotate(
                    y=Count('blog', distinct=True),  # unique blogs read
                    z=Count('id')  # total views
                )
                .order_by('-z')[:10]
                .values('x', 'y', 'z')
            )

        elif top_type == 'country':
            data = (
                qs.values(x=Coalesce(F('viewer_country__name'), Value('Unknown')))
                .annotate(
                    y=Count('blog', distinct=True),
                    z=Count('id')
                )
                .order_by('-z')[:10]
                .values('x', 'y', 'z')
            )

        elif top_type == 'blog':
            data = (
                qs.values(x=F('blog__title'))
                .annotate(
                    y=Value(1),
                    z=Count('id')
                )
                .order_by('-z')[:10]
                .values('x', 'y', 'z')
            )

        else:
            return Response(
                {"error": "Invalid top type. Use 'user', 'country', or 'blog'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(list(data))

    # performance views
    @action(detail=False, methods=["get"], url_path="performance")
    def performance(self, request):
        # Parameters
        compare = request.GET.get("compare", "month")  # month/week/day/year
        user_id = request.GET.get("user")

        # Base queryset with dynamic filters
        qs = BlogView.objects.select_related('blog', 'blog__author').filter(blog__isnull=False)

        if user_id:
            qs = qs.filter(blog__author_id=user_id)

        # Apply any additional dynamic filters
        qs = BlogViewFilter(request.query_params, queryset=qs).qs

        # Time trunc mapping
        trunc_map = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth, "year": TruncYear }
        trunc_fn = trunc_map.get(compare, TruncMonth)

        # Aggregate by period (ONE QUERY)
        period_qs = (
            qs.annotate(period=trunc_fn("viewed_at"))
            .values("period")
            .annotate(
                views=Count("id"),
                blogs_count=Count("blog", distinct=True),
            )
            .order_by("period")
        )

        period_list = list(period_qs)  # Execute query once

        # Compute previous period values (growth)
        prev_views = None
        prev_blogs = None
        results = []

        for row in period_list:
            views = row["views"]
            blogs_count = row["blogs_count"]

            growth_views = None if prev_views in (None, 0) else round((views - prev_views) / prev_views * 100, 2)
            growth_blogs = None if prev_blogs in (None, 0) else round((blogs_count - prev_blogs) / prev_blogs * 100, 2)

            # Format x/y/z
            results.append({
                "x": row["period"].strftime("%Y-%m-%d"),  # period label
                "y": blogs_count,  # number of blogs
                "z": views,  # total views
            })

        return Response(results)





