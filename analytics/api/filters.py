import django_filters
from ..models import BlogView

class BlogViewFilter(django_filters.FilterSet):
    viewed_at_gte = django_filters.IsoDateTimeFilter(field_name="viewed_at", lookup_expr='gte')
    viewed_at_lte = django_filters.IsoDateTimeFilter(field_name="viewed_at", lookup_expr='lte')

    blog_author = django_filters.NumberFilter(field_name="blog__author_id")
    blog_country = django_filters.CharFilter(field_name="blog__country__code")
    viewer_country = django_filters.CharFilter(field_name="viewer_country__code")
    user = django_filters.NumberFilter(field_name="user_id")

    class Meta:
        model = BlogView
        fields = []
