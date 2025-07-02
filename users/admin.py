from django.contrib import admin
from users.models import Photographer


# Register your models here.
@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    ...