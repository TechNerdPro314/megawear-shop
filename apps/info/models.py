# apps/info/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from ckeditor.fields import RichTextField

class BlogPost(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Slug", max_length=255, unique=True)
    short_description = models.TextField("Краткое описание", blank=True, help_text="Отображается в списке")
    content = RichTextField("Содержание")
    image = models.ImageField("Изображение", upload_to="blog/", blank=True, null=True)
    published_at = models.DateTimeField("Дата публикации", auto_now_add=True)
    is_active = models.BooleanField("Опубликована", default=True)

    class Meta:
        verbose_name = "Статья блога"
        verbose_name_plural = "Статьи блога"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)