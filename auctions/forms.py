from django import forms
from .models import Auction, Bid


class AuctionCreateForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['photo', 'start_time', 'end_time', 'starting_bid']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']