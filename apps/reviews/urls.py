from django.urls import path
from .views import (
    add_review_view,
    product_reviews_view,
    my_reviews_view,
    helpful_review_view,
    not_helpful_review_view,
)

app_name = "reviews"

urlpatterns = [
    path("add/<int:product_id>/", add_review_view, name="add_review"),
    path("product/<int:product_id>/", product_reviews_view, name="product_reviews"),
    path("my/", my_reviews_view, name="my_reviews"),
    path("helpful/<int:review_id>/", helpful_review_view, name="helpful_review"),
    path("not-helpful/<int:review_id>/", not_helpful_review_view, name="not_helpful_review"),
]
