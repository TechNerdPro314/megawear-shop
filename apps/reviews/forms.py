from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'text']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} ⭐') for i in range(1, 6)]),
            'title': forms.TextInput(attrs={'placeholder': 'Заголовок отзыва'}),
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Поделитесь впечатлениями о товаре...'}),
        }
        labels = {
            'rating': 'Оценка',
            'title': 'Заголовок',
            'text': 'Отзыв',
        }