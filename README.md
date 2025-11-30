Blog Analytics API

A high-performance Django REST Framework analytics system for blog applications.
It provides aggregated insights based on blog views, authors, and countries, with single-query optimized performance and flexible filtering capabilities.

Overview

This API exposes three major analytics endpoints:

Blog Views Analytics – grouped by country or user

Top Analytics – top 10 authors, countries, or blogs by views

Performance Analytics – time-series performance with growth percentage

The system is optimized to avoid N+1 queries and supports dynamic filtering with multiple operators.

Features

Optimized single-query aggregation

Dynamic filters for advanced querying

Time-range support: day, week, month, and year

Growth and decline percentage calculations

Clean DRF ViewSet-based structure

Installation Guide

Follow these steps to run the project locally.

Step 1 — Clone the Repository
git clone https://github.com/erdey2/blog-analytics-api.git
cd blog-analytics-api

Step 2 — Create Virtual Environment
python3 -m venv env
source env/bin/activate        # Linux/macOS
env\Scripts\activate           # Windows

Step 3 — Install Dependencies
pip install -r requirements.txt

Step 4 — Configure Environment Variables

Create a .env file:

SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=postgres://username:password@localhost:5432/blogdb

Or manually configure settings.py.

Step 5 — Apply Migrations
python manage.py migrate

Step 6 — Run Server
python manage.py runserver

API Endpoints

All analytics endpoints are served under the /analytics/ route.

Blog Views Analytics

Provides aggregated blog and view counts grouped by a specified object type.

Top Analytics

Returns top 10 records ranked by view count, grouped by user, country, or by individual blog.

Performance Analytics

Returns time-series performance data including blog count, total views, and growth percentage between periods.

Dynamic Filters

The API supports dynamic filter rules.
Supported operators include equality, inequality, inclusion, exclusion, greater-than, and less-than.

Filters follow a consistent format specifying:

the field

the operator

the value

Project Structure

The project is divided into apps that handle blogs, blog views, and analytics.
The analytics module includes views, serializers, and reusable filter utilities.