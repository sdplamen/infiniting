from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from photos.models import Photo
from users.forms import CustomUserCreationForm, PhotographerProfileForm, ProfileDetailForm, ProfileCommentForm
from users.mixins import UserIsProfileOwnerMixin, PaginationMixin
from users.models import Photographer, ProfileComment

UserModel = get_user_model()

# Create your views here.
class UserRegisterView(CreateView):
    model = UserModel
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Note: Signal for profile creation

        if response.status_code in [301, 302]:
            login(self.request, self.object)

        return response

class ProfileListView(ListView):
    template_name = 'users/profile-list.html'
    context_object_name = 'photographers'
    paginate_by = 10

    def get_queryset(self):
        return Photographer.objects.select_related('user').order_by('-created_at', '-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # one query for the follow buttons on the page, not one per profile
        user = self.request.user
        context['followed_user_ids'] = (
            set(user.following.values_list('followed_id', flat=True)) if user.is_authenticated else set())
        return context

class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Photographer
    form_class = PhotographerProfileForm
    template_name = 'users/profile-create.html'

    def form_valid(self, form):
        if Photographer.objects.filter(user=self.request.user).exists():
            form.add_error(None, 'You already have a photographer profile.')
            return self.form_invalid(form)
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('user-profile-detail', kwargs={'pk': self.object.pk})

from django.http import Http404


class ProfileDetailView(PaginationMixin, DetailView):
    queryset = Photographer.objects.select_related('user')
    template_name = 'users/profile-details.html'
    context_object_name = 'photographer'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        if self.kwargs.get(self.pk_url_kwarg) is None:
            if self.request.user.is_authenticated:
                try:
                    return self.queryset.get(user=self.request.user)
                except Photographer.DoesNotExist:
                    return None
            else:
                return None
        else:
            try:
                return super().get_object(queryset)
            except Http404:
                return None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None :
            if not self.request.user.is_authenticated :
                return redirect('login')
            elif self.kwargs.get(self.pk_url_kwarg) is None :
                return redirect('user-profile-create')
            else :
                return redirect('user-profile-list')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # dispatch() already loaded the profile; DetailView.get() would load it again
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # the photo cards: group, and like/comment/rating counts in the same query
        photos = (Photo.objects.filter(author=self.object).select_related('group')
                  .with_counts().order_by('-uploaded_at', '-pk'))
        pagination_context = self.get_paginated_queryset(photos, self.request)
        context.update(pagination_context)
        context['photos'] = context['page_obj']
        context['form'] = ProfileDetailForm(photographer=self.object, user=self.request.user)
        context['followers'] = self.object.user.followers.select_related('follower__photographer')
        context['following'] = self.object.user.following.select_related('followed__photographer')
        context['member_groups'] = self.object.user.user_groups.order_by('name')
        context['comments'] = self.object.comments.select_related('user__photographer')
        # drafts are shown only to their author and to approvers (same rule as the articles list)
        articles = self.object.articles.order_by('-created_at')
        viewer = self.request.user
        if not (viewer.id == self.object.user_id or viewer.has_perm('articles.can_approve_articles')):
            articles = articles.filter(is_approved=True)
        context['articles'] = articles
        # essays: published ones, plus drafts for their author
        essays = self.object.essays.annotate(frame_count=Count('items'))
        if viewer.id != self.object.user_id:
            essays = essays.filter(is_published=True)
        context['essays'] = essays
        context['comment_form'] = ProfileCommentForm()

        if self.request.user.is_authenticated:
            context['is_following_photographer'] = self.request.user.following.filter(
                followed=self.object.user).exists()
        else:
            context['is_following_photographer'] = False
        return context

class ProfileUpdateView(LoginRequiredMixin, UserIsProfileOwnerMixin, UpdateView):
    model = Photographer
    form_class = PhotographerProfileForm
    template_name = 'users/profile-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('user-profile-detail', kwargs={'pk': self.object.pk})

class ProfileDeleteView(LoginRequiredMixin, UserIsProfileOwnerMixin, DeleteView):
    model = Photographer
    template_name = 'users/profile-delete.html'
    success_url = reverse_lazy('photo-home')

    def get_object(self, queryset=None):
        return get_object_or_404(Photographer, user=self.request.user)

    def form_valid(self, form):
        user = self.request.user
        logout(self.request)
        messages.success(self.request, f'Профилът на {user.username} беше изтрит успешно.')
        return super().form_valid(form)


def _handle_follow_action(request, pk, action):
    user_to_handle = get_object_or_404(UserModel, pk=pk)

    if request.user == user_to_handle:
        messages.warning(request, 'Не можеш да последваш себе си.')
        return redirect('user-profile-detail', pk=pk)

    try:
        photographer_profile = user_to_handle.photographer
    except Photographer.DoesNotExist:
        messages.error(request, 'Този потребител няма фотографски профил.')
        return redirect('user-profile-list')

    if action == 'follow':
        if request.user.following.filter(followed=user_to_handle).exists():
            messages.info(request, f'Вие вече следвате {user_to_handle.username}.')
        else:
            request.user.following.create(followed=user_to_handle)
            messages.success(request, f'Вие следвате {user_to_handle.username}.')
    elif action == 'unfollow':
        if not request.user.following.filter(followed=user_to_handle).exists():
            messages.info(request, f'Вие не следвате {user_to_handle.username}.')
        else:
            request.user.following.filter(followed=user_to_handle).delete()
            messages.success(request, f'Вие вече не следвате {user_to_handle.username}.')

    return redirect('user-profile-detail', pk=photographer_profile.pk)


@login_required
@require_POST
def follow_user(request, pk):
    return _handle_follow_action(request, pk, 'follow')


@login_required
@require_POST
def unfollow_user(request, pk):
    return _handle_follow_action(request, pk, 'unfollow')


@login_required
@require_POST
def add_profile_comment(request, pk):
    photographer = get_object_or_404(Photographer, pk=pk)
    is_owner = request.user.id == photographer.user_id
    if not (is_owner or request.user.following.filter(followed_id=photographer.user_id).exists()):
        raise PermissionDenied  # only followers (and the owner, to reply) may comment
    form = ProfileCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.photographer = photographer
        comment.save()
    return redirect('user-profile-detail', pk=pk)


@login_required
@require_POST
def delete_profile_comment(request, pk, comment_pk):
    """The comment's writer or the profile's owner may delete a comment."""
    comment = get_object_or_404(ProfileComment.objects.select_related('photographer'), pk=comment_pk, photographer_id=pk)
    if request.user.id not in (comment.user_id, comment.photographer.user_id):
        raise PermissionDenied
    comment.delete()
    return redirect('user-profile-detail', pk=pk)
