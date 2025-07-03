from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from .forms import AuctionCreateForm, BidForm
from .models import Auction

# Create your views here.
class AuctionListView(ListView):
    model = Auction
    template_name = 'auctions/auction-list.html'
    context_object_name = 'auctions'
    ordering = ['-start_time']

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('photo__ratings__score')).order_by('-avg_rating')
        elif sort_by == 'likes':
            queryset = queryset.annotate(num_likes=Count('photo__likes')).order_by('-num_likes')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_options'] = ['latest', 'rating', 'likes']
        context['current_sort'] = self.request.GET.get('sort_by', 'latest')
        return context

class AuctionDetailView(DetailView):
    model = Auction
    template_name = 'auctions/auction-details.html'
    context_object_name = 'auction'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bids'] = self.object.bids.all()
        context['bid_form'] = BidForm()
        return context

class AuctionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Auction
    form_class = AuctionCreateForm
    template_name = 'auctions/auction-create.html'
    success_url = reverse_lazy('auction-list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

def place_bid(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            new_bid_amount = form.cleaned_data['amount']
            if new_bid_amount <= auction.current_highest_bid:
                form.add_error('amount', 'Your bid must be higher than the current highest bid.')
            elif new_bid_amount <= auction.starting_bid and auction.current_highest_bid == 0:
                form.add_error('amount', 'Your bid must be higher than the starting bid.')
            else:
                bid = form.save(commit=False)
                bid.auction = auction
                bid.bidder = request.user
                bid.save()
                auction.current_highest_bid = new_bid_amount
                auction.highest_bidder = request.user
                auction.save()
                return redirect('auction-detail', pk=auction.pk)
        return redirect('auction-detail', pk=auction.pk)
    return HttpResponseBadRequest('Invalid request method.')