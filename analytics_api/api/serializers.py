from rest_framework import serializers

class BlogViewsAnalyticsSerializer(serializers.Serializer):
    x = serializers.CharField()          # grouping key: country name or username
    y = serializers.IntegerField()       # number of blogs
    z = serializers.IntegerField()       # total views
