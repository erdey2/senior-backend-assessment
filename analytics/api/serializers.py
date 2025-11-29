from rest_framework import serializers

class BlogViewsAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()          # grouping key: country name or username
    y = serializers.IntegerField()       # number of blogs
    z = serializers.IntegerField()       # total views

class TopAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()
    y = serializers.IntegerField()  # blog or view count
    z = serializers.IntegerField()  # total views

class PerformanceAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()  # period label + number_of_blogs
    y = serializers.IntegerField()  # total views
    z = serializers.FloatField()  # growth percentage vs previous period
