from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, FormView
from auctions.forms import AuctionCreateForm, BidForm, AuctionPaymentForm, DeactivateAuctionForm
from auctions.mixins import StaffOrSuperuserRequiredMixin
from auctions.models import Auction

# Create your views here.
def can_user_bid(user, auction):
    if not user.is_authenticated:
        return False, 'Влезте, за да направите оферта.'
    if not auction.is_active:
        return False, 'Този аукцион е спрян.'
    if auction.end_time <= timezone.now():
        return False, 'Този аукцион е приключил.'
    if user == auction.photo.author.user:
        return False, 'Не можете да наддавате на Ваша снимка.'
    return True, ''

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
        auction = self.object
        user = self.request.user

        context['bids'] = auction.bids.all()
        context['now'] = timezone.now()

        can_bid, bid_message = can_user_bid(user, auction)
        context['can_bid'] = can_bid
        context['bid_section_message'] = bid_message

        if can_bid:
            context['bid_form'] = BidForm(auction=auction, bidder=user)
        else:
            context['bid_form'] = None

        context['can_show_admin_actions'] = user.is_authenticated and user.is_staff

        context['auction_ended'] = auction.end_time <= timezone.now()
        context['user_won_auction'] = user.is_authenticated and user == auction.highest_bidder

        return context

class AuctionCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    model = Auction
    form_class = AuctionCreateForm
    template_name = 'auctions/auction-create.html'
    success_url = reverse_lazy('auction-list')

@login_required
def place_bid(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    user = request.user
    can_bid_now, error_message = can_user_bid(user, auction)
    if not can_bid_now :
        messages.error(request, error_message)
        return redirect('auction-detail', pk=auction.pk)
    if request.method == 'POST':
        form = BidForm(request.POST, auction=auction, bidder=user)
        if form.is_valid() :
            bid = form.save(commit=False)
            bid.auction = auction
            bid.bidder = user
            bid.save()
            auction.current_highest_bid = bid.amount
            auction.highest_bidder = user
            auction.save()
            return redirect('auction-detail', pk=auction.pk)
        else :
            context = {
                'auction' :auction,
                'bid_form' :form,
                'bids' :auction.bids.all(),
                'now' :timezone.now(),
                'can_bid' :True,
                'bid_section_message' :"",
                'can_show_admin_actions' :user.is_authenticated and user.is_staff,
                'auction_ended' :auction.end_time <= timezone.now(),
                'user_won_auction' :user.is_authenticated and user == auction.highest_bidder
            }

            return render(request, 'auctions/auction-details.html', context)

    return HttpResponseBadRequest('Invalid request method.')

class AuctionDeactivateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, FormView):
    model = Auction
    form_class = DeactivateAuctionForm
    template_name = 'auctions/auction-deactivate.html'
    success_url = reverse_lazy('auction-list')

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        auction = get_object_or_404(self.model, pk=pk)
        context['auction'] = auction
        return context
    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        auction = get_object_or_404(self.model, pk=pk)

        if auction.is_active :
            auction.is_active = False
            auction.save()
        return super().form_valid(form)

class PaymentView(LoginRequiredMixin, FormView):
    model = Auction
    form_class = AuctionPaymentForm
    template_name = 'auctions/auction-payment.html'
    success_url = reverse_lazy('auction-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        auction = {
            'pk': pk,
            'photo': {'caption': 'Аукцион'}
        }
        context['auction'] = auction
        return context

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        auction = {
            'pk': pk,
            'photo': {'caption': 'Аукцион'}
        }

        card_number = form.cleaned_data['card_number']
        expiry = form.cleaned_data['expiry']
        cvc = form.cleaned_data['cvc']
        return super().form_valid(form)