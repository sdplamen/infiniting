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

class PaymentForm(forms.Form):
    full_name = forms.CharField(max_length=100, label='Име и фамилия')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Адрес за доставка')
    card_number = forms.CharField(max_length=16, min_length=16, label='Номер на карта')