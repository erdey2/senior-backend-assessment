from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, F, Value, Window, Case, When, ExpressionWrapper, FloatField, CharField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear, Coalesce, Concat, Lag, ExtractYear, ExtractMonth, ExtractDay
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
    @action(detail=False, methods=['get'], url_path='performance')
    def performance(self, request):
        compare = request.query_params.get('compare', 'month')
        user_id = request.query_params.get('user')

        qs = BlogView.objects.select_related('blog', 'blog__author').filter(blog__isnull=False)

        if user_id:
            qs = qs.filter(blog__author_id=user_id)

        qs = BlogViewFilter(request.query_params, queryset=qs).qs

        trunc_map = {'day': TruncDay, 'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear}
        trunc_func = trunc_map.get(compare, TruncMonth)

        data = (
            qs.annotate(period=trunc_func('viewed_at'))
            .values('period')
            .annotate(
                y=Count('id'),
                blogs_count=Count('blog', distinct=True),
                prev_y=Window(Lag(Count('id'), default=0), order_by=F('period').asc())
            )
            .annotate(
                z=Case(
                    When(prev_y=0, then=Value(None)),
                    default=ExpressionWrapper(
                        Round((F('y') - F('prev_y')) * 100.0 / F('prev_y'), 2),
                        output_field=FloatField()
                    )
                ),
                x=Concat(
                    ExtractYear('period'), Value('-'),
                    ExtractMonth('period'), Value('-'),
                    ExtractDay('period'), Value(' ('),
                    F('blogs_count'), Value(' blogs)'),
                    output_field=CharField()
                )
            )
            .order_by('period')
            .values('x', 'y', 'z')
        )

        return Response(list(data))
