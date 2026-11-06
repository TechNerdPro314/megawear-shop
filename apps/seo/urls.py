from django.urls import path
from .views import sitemap_view, robots_view

app_name = "seo"

urlpatterns = [
    path("sitemap.xml", sitemap_view, name="sitemap"),
    path("robots.txt", robots_view, name="robots"),
]
