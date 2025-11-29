from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True)  # e.g., 'ET'

class Blog(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    created_at = models.DateTimeField(auto_now_add=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name='blogs')  # Blog's country

class View(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='views')
    viewer_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
