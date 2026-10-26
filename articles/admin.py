from django.contrib import admin
from articles.models import Article


# Register your models here.
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    fields = ('title', 'content', 'author')
    search_fields = ('title', 'content')
    ordering = ('author',)