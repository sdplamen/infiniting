from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from photos.forms import PhotoUploadForm, CommentForm, RatingForm, PhotoDetailForm
from photos.models import Photo, Like, Rating
from users.models import Photographer
from photos.mixins import UserIsObjectAuthorMixin, PhotoFormProcessingMixin, PaginationMixin
from django.core.files.storage import default_storage
from PIL import Image
from PIL.ExifTags import TAGS


# Create your views here.
class IndexView(PaginationMixin, ListView):
    model = Photo
    template_name = 'photos/photo-list.html'
    context_object_name = 'photos'
    ordering = ['-uploaded_at']
    paginate_by = 5

# def full_photo_view(request, photo_id):
#     photo = get_object_or_404(Photo, id=photo_id)
#     return render(request, 'photo-full-photo.html', {'photo': photo})

class FullPhotoView(DetailView):
    model = Photo
    template_name = 'photos/photo-full-photo.html'
    context_object_name = 'photo'


class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'photos/photo-detail.html'
    context_object_name = 'photo'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.object

        exif_data = {}
        if photo.image :
            try :
                with default_storage.open(photo.image.name, 'rb') as f :
                    image = Image.open(f)

                    exif_raw = image._getexif()

                    if exif_raw :
                        for tag_id, value in exif_raw.items() :
                            tag_name = TAGS.get(tag_id, tag_id)
                            exif_data[tag_name] = value
            except (IOError, AttributeError, KeyError) :
                pass

        context['exif_data'] = exif_data
        context['comments'] = self.object.comments.all().order_by('-created_at')
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