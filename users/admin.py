from django.contrib import admin
from users.models import Photographer


# Register your models here.
@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'name')
    filter = ('name', 'bio', 'profile_picture')
    search_fields = ('user', 'name')
    ordering = ('user',)