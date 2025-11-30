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

Time-range support: day, week, month, year

Growth and decline percentage calculations

Clean DRF ViewSet-based structure

Test Deployed API

The deployed API is available here:
https://blog-analysis.onrender.com

Example requests:

Blog Views Analytics
curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?object_type=user&range=month"

Top Analytics
curl -X GET "https://blog-analysis.onrender.com/analytics/top/?top=user&range=month"

Performance Analytics
curl -X GET "https://blog-analysis.onrender.com/analytics/performance/?compare=month"


Dynamic filters can be applied using the filters query parameter:

curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?filters={'blog__country__name':'Ethiopia'}"

Installation Guide (Local)

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

1. Blog Views Analytics

Aggregated blog and view counts grouped by a specified object type (country or user).

2. Top Analytics

Returns top 10 records ranked by view count, grouped by user, country, or individual blog.

3. Performance Analytics

Returns time-series performance data including:

Blog count

Total views

Growth percentage between periods

Dynamic Filters

Supports dynamic filter rules.
Supported operators: eq, neq, in, nin, gt, lt

Filter format:

{
  "field": "blog__author__username",
  "operator": "eq",
  "value": "user1"
}