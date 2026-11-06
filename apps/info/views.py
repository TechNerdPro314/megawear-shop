# apps/info/views.py
from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone
from apps.promotions.models import Coupon
from apps.cart.services import DELIVERY_OPTIONS
from .models import BlogPost


class PromoListView(ListView):
    template_name = 'info/promo.html'
    context_object_name = 'coupons'
    queryset = Coupon.objects.filter(
        active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now(),
    ).order_by('-valid_from')


class DeliveryView(TemplateView):
    template_name = 'info/delivery_payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delivery_options'] = DELIVERY_OPTIONS
        return context


class WarrantyView(TemplateView):
    template_name = 'info/warranty_returns.html'


class ContactsView(TemplateView):
    template_name = 'info/contacts.html'


class AboutView(TemplateView):
    template_name = 'info/about.html'


class BlogListView(ListView):
    """Список статей блога"""
    template_name = 'info/blog.html'
    context_object_name = 'posts'
    queryset = BlogPost.objects.filter(is_active=True)
    paginate_by = 6


class BlogDetailView(DetailView):
    """Детальная страница статьи"""
    model = BlogPost
    template_name = 'info/blog_detail.html'
    context_object_name = 'post'