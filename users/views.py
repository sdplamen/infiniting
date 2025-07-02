from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .forms import CustomUserCreationForm, PhotographerProfileForm
from .models import Photographer


# Create your views here.
class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

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
        # Check for existing profile
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
        return context

class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Photographer
    form_class = PhotographerProfileForm
    template_name = 'users/profile-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('user-profile-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        return self.request.user == self.get_object().user

class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Photographer
    template_name = 'users/profile-delete.html'
    success_url = reverse_lazy('photo-home')

    def test_func(self):
        return self.request.user == self.get_object().user