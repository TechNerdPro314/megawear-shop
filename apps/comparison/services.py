# apps/comparison/services.py
class ComparisonService:
    SESSION_KEY = 'comparison_list'

    def __init__(self, request):
        self.session = request.session
        self.list = self.session.get(self.SESSION_KEY, [])

    def add(self, product_id):
        if product_id not in self.list:
            self.list.append(product_id)
            self.session[self.SESSION_KEY] = self.list
            return True
        return False

    def remove(self, product_id):
        if product_id in self.list:
            self.list.remove(product_id)
            self.session[self.SESSION_KEY] = self.list
            return True
        return False

    def clear(self):
        self.session[self.SESSION_KEY] = []
        self.list = []

    def get_products(self):
        from apps.catalog.models import Product
        return Product.objects.filter(id__in=self.list, is_active=True).prefetch_related('attribute_values__attribute')

    def __iter__(self):
        return iter(self.get_products())

    def __len__(self):
        return len(self.list)

    def has_items(self):
        return len(self.list) > 0