from django.contrib import admin
from auctions.models import Auction, AuctionComment


# Register your models here.
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('photo', 'highest_bidder_id', 'created_at', 'updated_at')
    filter = ('is_active',)
    search_fields = ('auction', 'amount')
    ordering = ('highest_bidder_id',)

class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount')
    filter = ('bid_time',)


@admin.register(AuctionComment)
class AuctionCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'auction', 'created_at')
    search_fields = ('text',)
