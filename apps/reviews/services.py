from django.db.models import Avg, Count
from django.utils import timezone
from apps.orders.models import Order, OrderStatus


class ReviewService:
    """Сервис для управления отзывами"""
    
    @staticmethod
    def can_user_review_product(user, product) -> bool:
        """Проверяет, может ли пользователь оставить отзыв о товаре"""
        if not user.is_authenticated:
            return False
        
        # Проверка: уже есть ли отзыв
        from apps.reviews.models import Review
        if Review.objects.filter(product=product, user=user).exists():
            return False
        
        return True
    
    @staticmethod
    def is_verified_purchase(user, product) -> bool:
        """Проверяет, покупал ли пользователь товар"""
        return Order.objects.filter(
            user=user,
            status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
            items__product=product
        ).exists()
    
    @staticmethod
    def get_average_rating(product):
        """Средний рейтинг товара"""
        from apps.reviews.models import Review
        result = Review.objects.filter(
            product=product,
            status="approved"
        ).aggregate(avg=Avg("rating"))
        return result["avg"] or 0
    
    @staticmethod
    def get_rating_distribution(product):
        """Распределение оценок по 1-5"""
        from apps.reviews.models import Review
        distribution = Review.objects.filter(
            product=product,
            status="approved"
        ).values("rating").annotate(count=Count("id")).order_by("-rating")
        
        return {i: 0 for i in range(1, 6)} | {item["rating"]: item["count"] for item in distribution}
    
    @staticmethod
    def get_reviews_count(product):
        """Общее количество одобренных отзывов"""
        from apps.reviews.models import Review
        return Review.objects.filter(product=product, status="approved").count()
    
    @staticmethod
    def get_user_reviews(user, status=None):
        """Получить отзывы пользователя"""
        from apps.reviews.models import Review
        qs = Review.objects.filter(user=user).select_related("product")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")
