from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from photos.models import Photo

User = get_user_model()
# Create your models here.
class Auction(models.Model) :
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name='auction')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_highest_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    highest_bidder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='auctions_won')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) :
        return f'Auction for Photo {self.photo.id}'

    @property
    def is_open(self):
        """Active and not yet ended: bidding and comments are possible."""
        return self.is_active and self.end_time > timezone.now()

    @property
    def comments_open(self):
        """Comments are allowed until the auction ends or staff deactivate it."""
        return self.is_open


class Bid(models.Model) :
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    class Meta :
        ordering = ['-bid_time']

    def __str__(self) :
        return f'{self.bidder.username} bid {self.amount} on {self.auction.photo.id}'


class AuctionComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auction_comments')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on auction {self.auction_id}'
