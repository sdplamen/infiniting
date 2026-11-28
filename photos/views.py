from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from photos.forms import PhotoUploadForm, CommentForm, RatingForm, PhotoDetailForm
from photos.models import Photo, Like, Rating, Comment
from users.models import Photographer
from photos.mixins import UserIsObjectAuthorMixin, PhotoFormProcessingMixin


class IndexView(ListView):
    """The home feed. ListView paginates (one COUNT, one page query); the cards'
    author names come in the same query, so the count stays flat per page."""
    template_name = 'photos/photo-list.html'
    context_object_name = 'photos'
    paginate_by = 5

    def get_queryset(self):
        return Photo.objects.for_cards().order_by('-uploaded_at', '-pk')

class FullPhotoView(DetailView):
    """Dark-room lightbox: one photo on #0d0d0d, with its neighbours in feed
    order (newest first) for ←/→ and a loupe (static/js/lightbox.js).

    `?back=<path>` names the page Esc returns to (e.g. the auction page);
    without it Esc goes to the detail page of the photo being shown.
    `?essay=<pk>` steps through that essay's sequence instead of the feed,
    and Esc returns to the essay at the frame being shown."""
    model = Photo
    template_name = 'photos/photo-full-photo.html'
    context_object_name = 'photo'

    def _essay(self):
        essay_id = self.request.GET.get('essay', '')
        if not essay_id.isdigit():
            return None
        from essays.models import Essay
        return Essay.visible_to(self.request.user).filter(pk=essay_id).first()

    def _back_url(self):
        back = self.request.GET.get('back', '')
        if back and url_has_allowed_host_and_scheme(back, allowed_hosts={self.request.get_host()},
                                                    require_https=self.request.is_secure()):
            return back
        return ''

    def _lightbox_url(self, photo, back, essay=None):
        url = reverse('photo-full-photo', kwargs={'pk': photo.pk})
        params = {key: value for key, value in (('essay', essay.pk if essay else ''), ('back', back)) if value}
        return f'{url}?{urlencode(params)}' if params else url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.object
        back = self._back_url()

        essay = self._essay()
        sequence = list(essay.items.values_list('photo_id', flat=True)) if essay else []
        if photo.pk in sequence:
            # inside an essay: its order, its count, and Esc back to this frame
            index = sequence.index(photo.pk)
            prev_pk = sequence[index - 1] if index > 0 else None
            next_pk = sequence[index + 1] if index + 1 < len(sequence) else None
            neighbours = Photo.objects.in_bulk([pk for pk in (prev_pk, next_pk) if pk])
            prev_photo, next_photo = neighbours.get(prev_pk), neighbours.get(next_pk)
            context.update({
                'essay': essay,
                'prev_photo': prev_photo,
                'next_photo': next_photo,
                'prev_url': self._lightbox_url(prev_photo, back, essay) if prev_photo else '',
                'next_url': self._lightbox_url(next_photo, back, essay) if next_photo else '',
                'close_url': back or f"{reverse('essay-detail', kwargs={'pk': essay.pk})}#frame-{index + 1}",
                'position': index + 1,
                'total': len(sequence),
            })
            return context

        # same order as the home feed: -uploaded_at, ties broken by -pk
        newer = Q(uploaded_at__gt=photo.uploaded_at) | Q(uploaded_at=photo.uploaded_at, pk__gt=photo.pk)
        older = Q(uploaded_at__lt=photo.uploaded_at) | Q(uploaded_at=photo.uploaded_at, pk__lt=photo.pk)
        prev_photo = Photo.objects.filter(newer).order_by('uploaded_at', 'pk').first()
        next_photo = Photo.objects.filter(older).order_by('-uploaded_at', '-pk').first()

        context.update({
            'prev_photo': prev_photo,
            'next_photo': next_photo,
            'prev_url': self._lightbox_url(prev_photo, back) if prev_photo else '',
            'next_url': self._lightbox_url(next_photo, back) if next_photo else '',
            'close_url': back or reverse('photo-detail', kwargs={'pk': photo.pk}),
            'position': Photo.objects.filter(newer).count() + 1,
            'total': Photo.objects.count(),
        })
        return context


class PhotoDetailView(DetailView):
    template_name = 'photos/photo-detail.html'
    context_object_name = 'photo'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Photo.objects.for_cards().with_counts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('user__photographer').order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['rating_form'] = RatingForm()

        user_liked = False
        user_rating = None

        if self.request.user.is_authenticated:
            photographer = getattr(self.request.user, 'photographer', None)
            if photographer:
                user_liked = Like.objects.filter(photo=self.object, user=self.request.user).exists()
                user_rating = Rating.objects.filter(photo=self.object, user=photographer).first()

        context['form'] = PhotoDetailForm(
            photo=self.object,
            user=self.request.user,
            user_liked=user_liked,
            user_rating=user_rating
        )
        return context

class PhotoCreateView(LoginRequiredMixin, CreateView):
    model = Photo
    form_class = PhotoUploadForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.request.user}
    template_name = 'photos/photo-create.html'
    success_url = reverse_lazy('photo-home')

    def form_valid(self, form):
        try:
            photographer = self.request.user.photographer
        except Photographer.DoesNotExist:
            form.add_error(None, 'You need a photographer profile to upload photos.')
            return self.form_invalid(form)
        form.instance.author = photographer
        return super().form_valid(form)

class PhotoUpdateView(LoginRequiredMixin, UserIsObjectAuthorMixin, UpdateView):
    model = Photo
    form_class = PhotoUploadForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.request.user}
    template_name = 'photos/photo-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('photo-detail', kwargs={'pk': self.object.pk})

class PhotoDeleteView(LoginRequiredMixin, UserIsObjectAuthorMixin, DeleteView):
    model = Photo
    template_name = 'photos/photo-delete.html'
    success_url = reverse_lazy('photo-home')
    pk_url_kwarg = 'pk'

def _handle_photo_like_action(request, pk, action_type):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        if request.user.is_authenticated:
            if action_type == 'like':
                Like.objects.get_or_create(user=request.user, photo=photo)
            elif action_type == 'unlike':
                Like.objects.filter(user=request.user, photo=photo).delete()
            return redirect('photo-detail', pk=photo.pk)
        else:
            return redirect('login')

@login_required
def like_photo(request, pk):
    return _handle_photo_like_action(request, pk, 'like')

@login_required
def unlike_photo(request, pk):
    return _handle_photo_like_action(request, pk, 'unlike')

class PhotoAddCommentView(PhotoFormProcessingMixin):
    form_class = CommentForm
    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.user = self.request.user
        comment.photo = self.object
        comment.save()
        return super().form_valid(form)

class PhotoAddRatingView(PhotoFormProcessingMixin):
    form_class = RatingForm
    def form_valid(self, form):
        Rating.objects.update_or_create(
            user=self.request.user.photographer,
            photo=self.object,
            defaults={'score': form.cleaned_data['score']}
        )
        return super().form_valid(form)


@login_required
@require_POST
def delete_comment(request, pk, comment_pk):
    """The comment's writer or the photo's author may delete a comment."""
    comment = get_object_or_404(Comment.objects.select_related('photo__author'), pk=comment_pk, photo_id=pk)
    if request.user.id not in (comment.user_id, comment.photo.author.user_id):
        raise PermissionDenied
    comment.delete()
    return redirect('photo-detail', pk=pk)
