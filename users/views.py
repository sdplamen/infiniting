from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from users.forms import CustomUserCreationForm, PhotographerProfileForm, ProfileDetailForm
from users.mixins import UserIsProfileOwnerMixin
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

class ProfileDetailView(DetailView):
    model = Photographer
    template_name = 'users/profile-details.html'
    context_object_name = 'photographer'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        if self.kwargs.get(self.pk_url_kwarg) is None and self.request.user.is_authenticated:
            return get_object_or_404(Photographer, user=self.request.user)
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('-uploaded_at')
        context['form'] = ProfileDetailForm(photographer=self.object, user=self.request.user)
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