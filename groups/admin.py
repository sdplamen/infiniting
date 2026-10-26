from django.contrib import admin
from groups.models import Group


# Register your models here.
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    filter = ('created_at',)
    ordering = ('name',)