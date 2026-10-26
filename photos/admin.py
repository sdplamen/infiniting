from django.contrib import admin
from photos.models import Photo


# Register your models here.
@admin.register(Photo)
class PhotoPhotoAdmin(admin.ModelAdmin):
    list_display = ('author', 'group', 'image', 'caption')
    search_fields = ('caption', 'author')
    filter = ('caption',)
    ordering = ('author',)

class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo')
    filter = ('photo',)
    ordering = ('user')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'text')
    filter = ('photo','user')
    ordering = ('user')

class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'score')
    filter = ('photo', 'user')
    ordering = ('photo')