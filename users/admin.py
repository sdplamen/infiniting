from django.contrib import admin
from users.models import Photographer, ProfileComment


# Register your models here.
@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'name')
    filter = ('name', 'bio', 'profile_picture')
    search_fields = ('user', 'name')
    ordering = ('user',)


@admin.register(ProfileComment)
class ProfileCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'photographer', 'created_at')
    search_fields = ('text',)
