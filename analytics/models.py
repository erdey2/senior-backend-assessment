from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=2, unique=True)  # e.g., 'ET', 'US', 'GB'

class Blog(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name='blogs')  # Blog's country

class BlogView(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='views')
    viewer_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
