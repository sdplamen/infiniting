from django.contrib import admin
from auctions.models import Auction


# Register your models here.
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    ...