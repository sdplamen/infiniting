from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, FormView
from auctions.forms import AuctionCreateForm, BidForm, AuctionPaymentForm, DeactivateAuctionForm, AuctionDetailForm
from auctions.mixins import StaffOrSuperuserRequiredMixin
from auctions.models import Auction

# Create your views here.
class AuctionListView(ListView):
    model = Auction
    template_name = 'auctions/auction-list.html'
    context_object_name = 'auctions'
    ordering = ['-start_time']
    paginate_by = 5

    # def get_queryset(self):
    #     queryset = Auction.objects.all().order_by('-start_time')

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        max_pages_to_show = 5

        start_page = max(1, page_obj.number - max_pages_to_show)
        end_page = min(paginator.num_pages, start_page + max_pages_to_show  + 1)

        if (end_page - start_page + 1) < max_pages_to_show :
            start_page = max(1, end_page - max_pages_to_show + 1)

        context['limited_page_range'] = range(start_page, end_page + 1)

        return context

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

        auction_detail_form = AuctionDetailForm(auction=auction, user=user)
        context['form'] = auction_detail_form

        if auction_detail_form.can_user_bid():
            context['bid_form'] = BidForm(auction=auction, bidder=user)
        else:
            context['bid_form'] = None

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

    auction_detail_form = AuctionDetailForm(auction=auction, user=user)
    if not auction_detail_form.can_user_bid():
        messages.error(request, 'Не можете да направите оферта за този аукцион.')
        return redirect('auction-detail', pk=auction.pk)

    if request.method == 'POST':
        form = BidForm(request.POST, auction=auction, bidder=user)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.auction = auction
            bid.bidder = user
            bid.save()
            auction.current_highest_bid = bid.amount
            auction.highest_bidder = user
            auction.save()
            messages.success(request, 'Вашата оферта беше приета успешно!')
            return redirect('auction-detail', pk=auction.pk)
        else:
            context = {
                'auction': auction,
                'bid_form': form,
                'bids': auction.bids.all(),
                'now': timezone.now(),
                'form': AuctionDetailForm(auction=auction, user=user),
            }
            return render(request, 'auctions/auction-details.html', context)

class AuctionDeactivateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, FormView):
    model = Auction
    form_class = DeactivateAuctionForm
    # template_name = 'auctions/auction-deactivate.html'
    success_url = reverse_lazy('auction-list')

    def get(self, request, *args, **kwargs):
        auction = get_object_or_404(self.model, pk=self.kwargs.get('pk'))
        if auction.is_active:
            auction.is_active = False
            auction.save()
            messages.success(request, f"Aукционът '{auction.pk}' е деактивиран.")
        else:
            messages.warning(request, 'Аукционът вече е деактивиран.')
        return self.redirect_to_success_url()

    def redirect_to_success_url(self):
        return redirect(self.success_url)

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
        auction = get_object_or_404(Auction, pk=pk)
        winner = auction.highest_bidder

        if self.request.user == winner:
            photographer = winner.photographer

            photo = auction.photo
            photo.author = photographer
            photo.save()

            auction.is_active = False
            auction.save()
            auction.delete()

            messages.success(self.request, f"Поздравления! Вие спечелихте аукциона и сте притежател на тази снимка: {photo.caption}.")
        else:
            messages.error(self.request, 'Вие не спечелихте тази аукцион.')

        return redirect(self.success_url)