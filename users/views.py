from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from photos.models import Photo
from users.forms import CustomUserCreationForm, PhotographerProfileForm, ProfileDetailForm
from users.mixins import UserIsProfileOwnerMixin, PaginationMixin
from users.models import Photographer

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
    model = Photographer
    template_name = 'users/profile-list.html'
    context_object_name = 'photographers'
    paginate_by = 10

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
    model = Photographer
    template_name = 'users/profile-details.html'
    context_object_name = 'photographer'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        if self.kwargs.get(self.pk_url_kwarg) is None:
            if self.request.user.is_authenticated:
                try:
                    return Photographer.objects.get(user=self.request.user)
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
        if self.object is None:
            if not self.request.user.is_authenticated:
                return redirect('login')
            elif self.kwargs.get(self.pk_url_kwarg) is None:
                return redirect('user-profile-create')
            else:
                return redirect('user-profile-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photos = Photo.objects.filter(author=self.object).order_by('-uploaded_at')

        pagination_context = self.get_paginated_queryset(photos, self.request)

        context.update(pagination_context)
        context['photos'] = context['page_obj']
        context['form'] = ProfileDetailForm(photographer=self.object, user=self.request.user)
        context['followers'] = self.object.user.followers.all()
        context['following'] = self.object.user.following.all()

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
