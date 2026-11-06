from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from health_check.views import MainView
from django.views.generic import TemplateView
from apps.info.views import PromoListView, DeliveryView, BlogListView, BlogDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ht/", MainView.as_view(), name="health_check"),

    path("", include("apps.catalog.urls")),
    path('info/terms/', TemplateView.as_view(template_name='info/terms.html'), name='info_terms'),
    path("users/", include("apps.users.urls")),
    path("cart/", include("apps.cart.urls")),
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),        # единственный раз
    path("promotions/", include("apps.promotions.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("importer/", include("apps.importer.urls")),
    path('info/contacts/', TemplateView.as_view(template_name='info/contacts.html'), name='info_contacts'),
    path('info/delivery/', DeliveryView.as_view(), name='info_delivery'),
    path('info/warranty/', TemplateView.as_view(template_name='info/warranty_returns.html'), name='info_warranty'),
    path('info/promo/', PromoListView.as_view(), name='info_promo'),
    path('info/blog/', BlogListView.as_view(), name='info_blog'),
    path('info/blog/<slug:slug>/', BlogDetailView.as_view(), name='info_blog_detail'),
    path('info/privacy/', TemplateView.as_view(template_name='info/privacy_policy.html'), name='info_privacy'),
    path("comparison/", include("apps.comparison.urls")),   # добавлено
    path("", include("apps.seo.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)