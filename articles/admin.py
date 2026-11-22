from django.contrib import admin
from articles.models import Article, ArticleComment


# Register your models here.
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    fields = ('title', 'content', 'author')
    search_fields = ('title', 'content')
    ordering = ('author',)


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'created_at')
    search_fields = ('text',)
