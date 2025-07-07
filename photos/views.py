from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .forms import PhotoUploadForm, CommentForm, RatingForm
from photos.models import Photo, Like, Comment, Rating
from users.models import Photographer

# Create your views here.
class IndexView(ListView):
    model = Photo
    template_name = 'photos/index.html'
    context_object_name = 'photos'
    ordering = ['-uploaded_at']
    paginate_by = 12

class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'photos/photo-detail.html'
    context_object_name = 'photo'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['rating_form'] = RatingForm()
        if self.request.user.is_authenticated:
            photographer = getattr(self.request.user, 'photographer', None)
            if photographer :
                context['user_liked'] = Like.objects.filter(photo=self.object, user=self.request.user).exists()
                context['user_rating'] = Rating.objects.filter(photo=self.object, user=photographer).first()
            else :
                context['user_liked'] = False
                context['user_rating'] = None
        return context

class PhotoCreateView(LoginRequiredMixin, CreateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'photos/photo-upload.html'
    success_url = reverse_lazy('photo-home')

    def form_valid(self, form):
        try:
            photographer = self.request.user.photographer
        except Photographer.DoesNotExist:
            form.add_error(None, 'You need a photographer profile to upload photos.')
            return self.form_invalid(form)
        form.instance.author = photographer
        return super().form_valid(form)

class PhotoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'photos/photo-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('photo-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        return self.request.user == self.get_object().author.user

class PhotoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Photo
    template_name = 'photos/photo-delete.html'
    success_url = reverse_lazy('photo-home')
    pk_url_kwarg = 'pk'

    def test_func(self):
        return self.request.user == self.get_object().author.user

@login_required
def like_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        Like.objects.get_or_create(user=request.user, photo=photo)
        return redirect('photo-detail', pk=photo.pk)
    return HttpResponseBadRequest('Invalid request method.')

@login_required
def unlike_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        Like.objects.filter(user=request.user, photo=photo).delete()
        return redirect('photo-detail', pk=photo.pk)
    return HttpResponseBadRequest('Invalid request method.')

@login_required
def add_comment(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.photo = photo
            comment.save()
            return redirect('photo-detail', pk=photo.pk)
        return redirect('photo-detail', pk=photo.pk)
    return HttpResponseBadRequest('Invalid request method.')

@login_required
def add_rating(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                user=request.user.photographer,
                photo=photo,
                defaults={'score': form.cleaned_data['score']}
            )
            return redirect('photo-detail', pk=photo.pk)
        return redirect('photo-detail', pk=photo.pk)
    return HttpResponseBadRequest('Invalid request method.')