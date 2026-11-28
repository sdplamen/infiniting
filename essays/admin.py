from django.contrib import admin
from essays.models import Essay, EssayItem


class EssayItemInline(admin.TabularInline):
    model = EssayItem
    extra = 0
    raw_id_fields = ['photo']


@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'kind', 'cover_layout', 'is_published', 'updated_at']
    list_filter = ['kind', 'is_published']
    search_fields = ['title', 'author__user__username']
    raw_id_fields = ['cover_photo']
    inlines = [EssayItemInline]
