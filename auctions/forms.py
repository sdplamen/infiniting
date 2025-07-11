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

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        self.bidder = kwargs.pop('bidder', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self) :
        amount = self.cleaned_data['amount']
        if amount <= self.auction.current_highest_bid :
            raise forms.ValidationError('Вашата оферта трябва да е по-висока от текущата най-висока оферта.')
        if amount <= self.auction.starting_bid and self.auction.current_highest_bid == 0 :
            raise forms.ValidationError('Вашата оферта трябва да е по-висока от началната оферта.')
        return amount

    def clean(self) :
        cleaned_data = super().clean()
        return cleaned_data

class DeactivateAuctionForm(forms.Form):
    ...

class AuctionPaymentForm(forms.Form):
    card_number = forms.CharField(
        label='Номер на карта',
        max_length=19,
        min_length=16,
        widget=forms.TextInput(attrs={
            'placeholder' :'1234 5678 9012 3456',
            'required' :True,
            'class' :'form-control'
        })
    )
    expiry = forms.CharField(
        label='Валидна до:',
        max_length=5,
        widget=forms.TextInput(attrs={
            'placeholder' :'MM/YY',
            'required' :True,
            'class' :'form-control'
        })
    )
    cvc = forms.CharField(
        label='CVC',
        max_length=4,
        min_length=3,
        widget=forms.TextInput(attrs={
            'placeholder' :'123',
            'required' :True,
            'class' :'form-control'
        })
    )

    def clean_expiry(self) :
        expiry = self.cleaned_data['expiry']
        if len(expiry) != 5 or expiry[2] != '/' :
            raise forms.ValidationError('Моля, въведете дата във формат MM/YY.')
        return expiry