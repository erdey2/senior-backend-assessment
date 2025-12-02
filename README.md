Blog Analytics API
A high-performance analytics system built with Django REST Framework, optimized for large-scale blog platforms.

Overview
This API exposes three core analytics endpoints:

1. Blog Views Analytics

Grouped analysis by country or user, with:

Total views

Number of unique blogs viewed

Full dynamic filtering

Time-range filtering (day/week/month/year)

2. Top Analytics

Top 10:

Authors

Countries

Blogs
Ranked by total views.

3. Performance Analytics

Time-series performance showing:

Blog count per period

Total views

Growth/decline percentages

Supports:

Day

Week

Month

Year

Features

✔ Optimized single-query ORM aggregation
✔ Zero N+1 queries
✔ Full dynamic filtering via django-filter
✔ Time ranges: day | week | month | year
✔ Growth/decline computation per period
✔ Clean ViewSet-based architecture
✔ DRF Spectacular-powered API documentation
✔ Deployed online for public testing

Live API (Deployed)

Base URL:
https://blog-analysis.onrender.com/analytics/

API Docs:
https://blog-analysis.onrender.com/api/docs/

Example API Requests
1. Blog Views Analytics

Group by user for the last month:
curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?object_type=user&range=month"

Group by country for the last 7 days:
curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?object_type=country&range=week"

With filters (viewer country = Ethiopia):
curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?viewer_country=ET&range=month"

2. Top Analytics

Top 10 users by views:
curl -X GET "https://blog-analysis.onrender.com/analytics/top/?top=user&range=month"

Top 10 countries:
curl -X GET "https://blog-analysis.onrender.com/analytics/top/?top=country&range=week"

Top 10 blogs:
curl -X GET "https://blog-analysis.onrender.com/analytics/top/?top=blog&range=month"

3. Performance Analytics
Monthly performance:
curl -X GET "https://blog-analysis.onrender.com/analytics/performance/?compare=month"

Performance for a specific author:
curl -X GET "https://blog-analysis.onrender.com/analytics/performance/?compare=week&user=3"

Dynamic Filtering
Supported query parameters include:

Parameter	Description
viewer_country	Filter by viewer country code
blog_country	Filter by blog country code
blog_author	Filter by author id
user	Filter by viewer user id
viewed_at_gte	Filter by start datetime
viewed_at_lte	Filter by end datetime

Example:
curl -X GET "https://blog-analysis.onrender.com/analytics/blog-views/?viewer_country=ET&viewed_at_gte=2025-10-01T00:00:00"

Installation & Setup (Local)

Follow these steps to run the analytics system locally.

Step 1 — Clone Repository
git clone https://github.com/erdey2/blog-analytics-api.git
cd blog-analytics-api

Step 2 — Create Virtual Environment
Linux/macOS:
python3 -m venv env
source env/bin/activate

Windows:
env\Scripts\activate

Step 3 — Install Dependencies
pip install -r requirements.txt

Step 4 — Configure Environment

Create a .env file:

SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://username:password@localhost:5432/blogdb

Or update settings.py manually.

Step 5 — Apply Migrations
python manage.py migrate

Step 6 — Populate Sample Data

Run:

python manage.py populate_sample_data


This will generate:

Users

Countries

Blogs

Blog view records

Useful for testing analytics without needing real traffic.

Step 7 — Run Server
python manage.py runserver


Server runs at:
http://127.0.0.1:8000/

API Endpoints Overview
Endpoint	Description
/analytics/blog-views/	Views grouped by country or user
/analytics/top/	Top 10 by views (users, countries, blogs)
/analytics/performance/	Time-series analytics with growth %