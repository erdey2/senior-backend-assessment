from rest_framework import serializers


class BlogViewsAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()
    y = serializers.IntegerField()
    z = serializers.IntegerField()

class TopAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()
    y = serializers.IntegerField()
    z = serializers.IntegerField()

class PerformanceAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()
    y = serializers.IntegerField()
    z = serializers.FloatField(allow_null=True)

