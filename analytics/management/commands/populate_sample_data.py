from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analytics.models import Country, Blog, BlogView
from random import randint, choice
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populate sample data: 10 users, 5 countries, 50 blogs, 1000 blog views'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to populate sample data...")

        # --- Create users ---
        users = []
        for i in range(1, 11):
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'email': f'user{i}@example.com'}
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        self.stdout.write("10 users created.")

        # --- Create countries ---
        country_data = [
            ('USA', 'US'),
            ('Ethiopia', 'ET'),
            ('India', 'IN'),
            ('Germany', 'DE'),
            ('Brazil', 'BR')
        ]
        countries = []
        for name, code in country_data:
            country, _ = Country.objects.get_or_create(name=name, code=code)
            countries.append(country)
        self.stdout.write("5 countries created.")

        # --- Create blogs ---
        blogs = []
        for i in range(1, 51):
            blog = Blog.objects.create(
                author=choice(users),
                country=choice(countries),
                title=f'Sample Blog Post {i}',
                content=f"This is sample content for blog post {i}."
            )
            blogs.append(blog)
        self.stdout.write("50 blogs created.")

        # --- Create blog views ---
        for _ in range(1000):
            BlogView.objects.create(
                blog=choice(blogs),
                viewer_country=choice(countries)
                # viewed_at is auto_now_add=True
            )
        self.stdout.write("1000 blog views created.")

        self.stdout.write(self.style.SUCCESS("Sample data population complete!"))
