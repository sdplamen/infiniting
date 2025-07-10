from django.http import HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, DetailView
from auctions.forms import AuctionCreateForm, BidForm, PaymentForm
from auctions.mixins import StaffOrSuperuserRequiredMixin
from auctions.models import Auction

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
        context['now'] = timezone.now()
        return context

class AuctionCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    model = Auction
    form_class = AuctionCreateForm
    template_name = 'auctions/auction-create.html'
    success_url = reverse_lazy('auction-list')

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

class AuctionDeactivateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, View):
    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        if auction.is_active:
            auction.is_active = False
            auction.save()
        return redirect('auction-list')

class PaymentView(LoginRequiredMixin, View):
    template_name = 'auctions/auction-payment.html'

    def get(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)
        form = PaymentForm()
        context = {'form': form, 'auction': auction}
        return render(request, self.template_name, context)

    def post(self, request, pk):
        auction = get_object_or_404(Auction, pk=pk)

        form = PaymentForm(request.POST)
        if form.is_valid():
            return redirect('auction-list')
        context = {'form': form, 'auction': auction}
        return render(request, self.template_name, context)