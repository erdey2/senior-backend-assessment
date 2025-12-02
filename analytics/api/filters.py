import django_filters
from ..models import BlogView

class BlogViewFilter(django_filters.FilterSet):
    viewed_at__gte = django_filters.DateTimeFilter(field_name="viewed_at", lookup_expr='gte')
    viewed_at__lte = django_filters.DateTimeFilter(field_name="viewed_at", lookup_expr='lte')
    blog__author = django_filters.NumberFilter(field_name="blog__author_id")
    blog__country = django_filters.CharFilter(field_name="blog__country__code")
    viewer_country = django_filters.CharFilter(field_name="viewer_country__code")
    user = django_filters.NumberFilter(field_name="user_id")

    class Meta:
        model = BlogView
        fields = []