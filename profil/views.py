from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from profil.forms import CustomUserCreationForm, PhotographerProfileForm, GroupCreateForm, CommentForm, RatingForm, PhotoUploadForm, ArticleForm, BidForm, AuctionCreateForm
from profil.models import Photo, Photographer, Group, Like, Rating, Article, Auction


class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

class IndexView(ListView):
    model = Photo
    template_name = 'index.html'
    context_object_name = 'latest-photos'
    ordering = ['-uploaded_at']
    paginate_by = 12

class PhotographerProfileListView(ListView):
    model = Photographer
    template_name = 'profile-list.html'
    context_object_name = 'photographer'
    paginate_by = 10

class PhotographerProfileCreateView(LoginRequiredMixin, CreateView):
    model = Photographer
    form_class = PhotographerProfileForm
    template_name = 'profile-create.html'
    success_url = reverse_lazy('profile-details')

    def form_valid(self, form):
        if Photographer.objects.filter(user=self.request.user).exists():
            form.add_error(None, 'You already have a photographer profile.')
            return self.form_invalid(form)
        form.instance.user = self.request.user
        return super().form_valid(form)

class PhotographerProfileDetailView(DetailView):
    model = Photographer
    template_name = 'profile-details.html'
    context_object_name = 'photographer-profile'
    slug_url_kwarg = 'profil_pk'
    pk_url_kwarg = 'profil_pk'

    def get_object(self, queryset=None):
        if self.kwargs.get(self.pk_url_kwarg) is None and self.request.user.is_authenticated :
            return get_object_or_404(Photographer, user=self.request.user)
        return super().get_object(queryset)

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('-uploaded_at')
        return context

class PhotographerProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Photographer
    form_class = PhotographerProfileForm
    template_name = 'profile-edit.html'
    slug_url_kwarg = 'profil_pk'
    pk_url_kwarg = 'profil_pk'

    def get_success_url(self) :
        return reverse_lazy('profile-details', kwargs={'profil_pk' :self.object.pk})

    def test_func(self) :
        profile = self.get_object()
        return self.request.user == profile.user

class PhotographerProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Photographer
    template_name = 'profile-delete.html'
    success_url = reverse_lazy('index')
    slug_url_kwarg = 'profil_pk'
    pk_url_kwarg = 'profil_pk'

    def test_func(self) :
        profile = self.get_object()
        return self.request.user == profile.user

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'group-create.html'
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        return response

class GroupListView(ListView):
    model = Group
    template_name = 'group-list.html'
    context_object_name = 'groups'
    paginate_by = 10

class GroupDetailView(DetailView):
    model = Group
    template_name = 'group-details.html'
    context_object_name = 'group'
    slug_url_kwarg = 'group_pk'
    pk_url_kwarg = 'group_pk'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('-uploaded_at')
        return context

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'group-edit.html'
    slug_url_kwarg = 'group_pk'
    pk_url_kwarg = 'group_pk'

    def get_success_url(self):
        return reverse_lazy('group-details', kwargs={'group_pk': self.object.pk})

    def test_func(self):
        group = self.get_object()
        return self.request.user in group.members.all()

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Group
    template_name = 'group_delete.html'
    success_url = reverse_lazy('group-list')
    slug_url_kwarg = 'group_pk'
    pk_url_kwarg = 'group_pk'

    def test_func(self):
        group = self.get_object()
        return self.request.user in group.members.all()

@login_required
def join_group(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    if request.method == 'POST':
        group.members.add(request.user)
        return redirect('group-details', group_pk=group.pk)
    return HttpResponseBadRequest('Invalid request method.')

@login_required
def leave_group(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    if request.method == 'POST':
        group.members.remove(request.user)
        return redirect('group-details', group_pk=group.pk)
    return HttpResponseBadRequest('Invalid request method.')

class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'photo-details.html'
    context_object_name = 'photo'
    pk_url_kwarg = 'photo_pk'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['rating_form'] = RatingForm()
        if self.request.user.is_authenticated :
            context['user_liked'] = Like.objects.filter(photo=self.object, user=self.request.user).exists()
            context['user_rating'] = Rating.objects.filter(photo=self.object, user=self.request.user).first()
        return context

class PhotoCreateView(LoginRequiredMixin, CreateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'photo-upload.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form) :
        try :
            photographer = self.request.user.photographer
        except Photographer.DoesNotExist :
            form.add_error(None, 'You need a photographer profile to upload photos. Please create one.')
            return self.form_invalid(form)
        form.instance.author = photographer
        return super().form_valid(form)

class PhotoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'photo-edit.html'
    pk_url_kwarg = 'photo_pk'

    def get_success_url(self):
        return reverse_lazy('photo-details', kwargs={'photo_pk': self.object.pk})

    def test_func(self) :
        photo = self.get_object()
        return self.request.user == photo.author

class PhotoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Photo
    template_name = 'photo-delete.html'
    success_url = reverse_lazy('index')
    pk_url_kwarg = 'photo_pk'

    def get_success_url(self):
        return reverse_lazy('photo-list')

    def test_func(self) :
        photo = self.get_object()
        return self.request.user == photo.author.user

@login_required
def like_photo(request, photo_pk):
    photo = get_object_or_404(Photo, pk=photo_pk)
    if request.method == 'POST':
        Like.objects.get_or_create(user=request.user, photo=photo)
    return redirect('photo-details', photo_pk=photo.pk)

@login_required
def unlike_photo(request, photo_pk):
    photo = get_object_or_404(Photo, pk=photo_pk)
    if request.method == 'POST':
        Like.objects.filter(user=request.user, photo=photo).delete()
    return redirect('photo-details', photo_pk=photo.pk)

@login_required
def add_comment(request, photo_pk):
    photo = get_object_or_404(Photo, pk=photo_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.photo = photo
            comment.save()
            return redirect('photo-details', photo_pk=photo.pk)
    return redirect('photo-details', photo_pk=photo.pk)

@login_required
def add_rating(request, photo_pk):
    photo = get_object_or_404(Photo, pk=photo_pk)
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                photo=photo,
                defaults={'score': form.cleaned_data['score']}
            )
            return redirect('photo-details', photo_pk=photo.pk)
    return redirect('photo-details', photo_pk=photo.pk)

class ArticleListView(ListView):
    model = Article
    template_name = 'article-list.html'
    context_object_name = 'articles'
    ordering = ['-created_at']
    paginate_by = 10

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'article-details.html'
    context_object_name = 'article'
    pk_url_kwarg = 'article_pk'

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article-create.html'
    success_url = reverse_lazy('article_list')

    def form_valid(self, form) :
        try :
            photographer = self.request.user.photographer
        except Photographer.DoesNotExist :
            form.add_error(None, 'You need a photographer profile to write articles. Please create one.')
            return self.form_invalid(form)
        form.instance.author = photographer
        return super().form_valid(form)

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article-edit.html'
    pk_url_kwarg = 'article_pk'

    def get_success_url(self):
        return reverse_lazy('article-details', kwargs={'article_pk': self.object.pk})

    def test_func(self) :
        article = self.get_object()
        return self.request.user == article.author.user

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'article-delete.html'
    success_url = reverse_lazy('article-list')
    pk_url_kwarg = 'article_pk'

    def get_success_url(self):
        return reverse_lazy('article-list')

    def test_func(self) :
        article = self.get_object()
        return self.request.user == article.author.user

class AuctionListView(ListView):
    model = Auction
    template_name = 'auction-list.html'
    context_object_name = 'auctions'
    ordering = ['-start_time']

    def get_queryset(self) :
        queryset = super().get_queryset().filter(is_active=True)
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'rating' :
            queryset = queryset.annotate(avg_rating=Avg('photo__ratings__score')).order_by('-avg_rating')
        elif sort_by == 'likes' :
            queryset = queryset.annotate(num_likes=Count('photo__likes')).order_by('-num_likes')
        return queryset

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['sort_options'] = ['latest', 'rating', 'likes']
        context['current_sort'] = self.request.GET.get('sort_by', 'latest')
        return context

class AuctionDetailView(DetailView):
    model = Auction
    template_name = 'auction-details.html'
    context_object_name = 'auction'
    pk_url_kwarg = 'auction_pk'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context['bids'] = self.object.bids.all()
        context['bid_form'] = BidForm()
        return context

@login_required
def place_bid(request, auction_pk):
    auction = get_object_or_404(Auction, pk=auction_pk)
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
                return redirect('auction-details', auction_pk=auction.pk)
    return redirect('auction-details', auction_pk=auction.pk)

class AuctionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Auction
    form_class = AuctionCreateForm
    template_name = 'auction-create.html'
    success_url = reverse_lazy('auction-list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        return super().form_valid(form)
