from django.contrib import admin
from auctions.models import Auction


# Register your models here.
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('photo', 'highest_bidder_id', 'created_at', 'updated_at')
    filter = ('is_active',)
    ordering = ('highest_bidder_id',)

class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount')
    filter = ('bid_time',)