from rest_framework import serializers

class BlogViewsAnalyticsSerializer(serializers.Serializer):
    name = serializers.CharField()
    y = serializers.IntegerField(source="unique_blogs")
    z = serializers.IntegerField(source="total_views")

class TopAnalyticsSerializer(serializers.Serializer):
    name = serializers.CharField()
    z = serializers.IntegerField(source="total_views")

class PerformanceAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()
    y = serializers.IntegerField()
    z = serializers.FloatField(allow_null=True)
    blogs_count = serializers.IntegerField()
