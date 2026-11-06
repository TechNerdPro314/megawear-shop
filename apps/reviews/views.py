from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count

from apps.catalog.models import Product
from apps.orders.models import Order, OrderStatus
from .models import Review


@login_required
def add_review_view(request, product_id):
    """Добавление отзыва о товаре"""
    product = get_object_or_404(Product, id=product_id)

    # Проверка: может ли пользователь написать отзыв
    if not request.user.is_authenticated:
        messages.error(request, "Для написания отзыва необходимо авторизоваться.")
        return redirect("users:login")

    # Проверка: уже есть ли отзыв
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "Вы уже оставляли отзыв о этом товаре.")
        return redirect(product.get_absolute_url())

    # Проверка: покупал ли пользователь товар
    has_bought = Order.objects.filter(
        user=request.user,
        status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
        items__product=product
    ).exists()

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating = int(request.POST.get("rating", 5))

        if not text:
            messages.error(request, "Введите текст отзыва.")
            return redirect(product.get_absolute_url())

        if not (1 <= rating <= 5):
            messages.error(request, "Укажите корректную оценку от 1 до 5.")
            return redirect(product.get_absolute_url())

        # Определяем заказ, если есть
        order = None
        if has_bought:
            order = Order.objects.filter(
                user=request.user,
                status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
                items__product=product
            ).first()

        review = Review.objects.create(
            product=product,
            user=request.user,
            title=title,
            text=text,
            rating=rating,
            is_verified_purchase=has_bought,
            order=order,
            status="approved" if has_bought else "pending"  # Без покупки - на модерации
        )

        if has_bought:
            messages.success(request, "Спасибо за ваш отзыв!")
        else:
            messages.info(request, "Ваш отзыв отправлен на модерацию.")

        return redirect(product.get_absolute_url())

    # Формируем контекст для формы
    return render(request, "reviews/add_review.html", {
        "product": product,
        "has_bought": has_bought,
    })


@require_POST
@login_required
def helpful_review_view(request, review_id):
    """Голосование 'полезно' за отзыв"""
    review = get_object_or_404(Review, id=review_id)
    
    # Проверка: не голосовал ли уже
    session_key = f"helpful_{review_id}"
    if session_key in request.session:
        return JsonResponse({"error": "Вы уже голосовали за этот отзыв"}, status=400)
    
    review.helpful_count += 1
    review.save(update_fields=["helpful_count"])
    
    request.session[session_key] = True
    
    return JsonResponse({"helpful_count": review.helpful_count})


@require_POST
@login_required
def not_helpful_review_view(request, review_id):
    """Голосование 'не полезно' за отзыв"""
    review = get_object_or_404(Review, id=review_id)
    
    session_key = f"not_helpful_{review_id}"
    if session_key in request.session:
        return JsonResponse({"error": "Вы уже голосовали за этот отзыв"}, status=400)
    
    review.not_helpful_count += 1
    review.save(update_fields=["not_helpful_count"])
    
    request.session[session_key] = True
    
    return JsonResponse({"not_helpful_count": review.not_helpful_count})


def product_reviews_view(request, product_id):
    """Список отзывов о товаре"""
    product = get_object_or_404(Product, id=product_id)
    
    # Получаем одобренные отзывы
    reviews = Review.objects.filter(
        product=product,
        status="approved"
    ).select_related("user").order_by("-created_at")
    
    # Фильтрация по рейтингу
    rating_filter = request.GET.get("rating")
    if rating_filter and rating_filter.isdigit():
        reviews = reviews.filter(rating=int(rating_filter))
    
    # Сортировка
    sort_by = request.GET.get("sort", "-created_at")
    if sort_by == "helpful":
        reviews = reviews.order_by("-helpful_count", "-created_at")
    elif sort_by == "newest":
        reviews = reviews.order_by("-created_at")
    elif sort_by == "oldest":
        reviews = reviews.order_by("created_at")
    
    # Расчет рейтинга
    avg_rating = Review.get_average_rating(product)
    rating_distribution = Review.get_rating_distribution(product)
    total_reviews = reviews.count()
    
    return render(request, "reviews/product_reviews.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1),
        "rating_distribution": rating_distribution,
        "total_reviews": total_reviews,
    })


@login_required
def my_reviews_view(request):
    """Список отзывов пользователя"""
    reviews = Review.objects.filter(
        user=request.user
    ).select_related("product").order_by("-created_at")
    
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})
