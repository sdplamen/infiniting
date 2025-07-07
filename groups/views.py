from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .forms import GroupCreateForm
from .models import Group

# Create your views here.
class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'groups/group-create.html'
    success_url = reverse_lazy('group-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        return response

class GroupListView(ListView):
    model = Group
    template_name = 'groups/group-list.html'
    context_object_name = 'groups'
    paginate_by = 10

class GroupDetailView(DetailView):
    model = Group
    template_name = 'groups/group-detail.html'
    context_object_name = 'group'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('-uploaded_at')
        return context

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'groups/group-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('group-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        return self.request.user in self.get_object().members.all()

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Group
    template_name = 'groups/group-delete.html'
    success_url = reverse_lazy('group-list')  # Corrected

    def test_func(self):
        return self.request.user in self.get_object().members.all()

def join_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.members.add(request.user)
        return redirect('group-detail', pk=group.pk)
    return HttpResponseBadRequest('Invalid request method.')

def leave_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.members.remove(request.user)
        return redirect('group-detail', pk=group.pk)
    return HttpResponseBadRequest('Invalid request method.')