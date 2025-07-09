from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from photos.models import Photo


class UserIsObjectAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().author.user

class PhotoFormProcessingMixin(LoginRequiredMixin, SingleObjectMixin, FormMixin, View):
    model = Photo
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('photo-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return redirect(self.get_success_url())

    def form_valid(self, form):
        return redirect(self.get_success_url())