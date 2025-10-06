from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from groups.forms import GroupCreateForm, GroupDetailForm
from groups.mixins import GroupMemberRequiredMixin
from groups.models import Group
from users.mixins import PaginationMixin


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


class GroupListView(PaginationMixin, ListView):
    model = Group
    template_name = 'groups/group-list.html'
    context_object_name = 'groups'
    paginate_by = 5

    def get_queryset(self):
        return Group.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        pagination_data = self.get_paginated_queryset(queryset, self.request)
        context.update(pagination_data)
        return context

class GroupDetailView(PaginationMixin, DetailView):
    model = Group
    template_name = 'groups/group-detail.html'
    context_object_name = 'group'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photos = self.object.photos.all().order_by('-uploaded_at')
        pagination_data = self.get_paginated_queryset(photos, self.request)
        context.update(pagination_data)
        context['photos'] = context['page_obj']
        context['form'] = GroupDetailForm(group=self.object, user=self.request.user)
        return context

class GroupUpdateView(LoginRequiredMixin, GroupMemberRequiredMixin, UpdateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'groups/group-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('group-detail', kwargs={'pk': self.object.pk})

class GroupDeleteView(LoginRequiredMixin, GroupMemberRequiredMixin, DeleteView):
    model = Group
    template_name = 'groups/group-delete.html'
    success_url = reverse_lazy('group-list')  # Corrected

def _handle_group_membership_change(request, pk, action_type):
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        if request.user.is_authenticated:
            if action_type == 'add':
                group.members.add(request.user)
            elif action_type == 'remove':
                group.members.remove(request.user)
            return redirect('group-detail', pk=group.pk)
        else:
            return redirect('login')


def join_group(request, pk):
    return _handle_group_membership_change(request, pk, 'add')

def leave_group(request, pk):
    return _handle_group_membership_change(request, pk, 'remove')

class GroupApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        if not group.is_approved and group.author:
            group.is_approved = True
            group.save()
            subject = f'Вашата група {group.name} беше одобрена за ползване!'
            message = f'Скъпи {group.author.username},\n\nВашата група {group.name} беше одобрена и вече може да бъде обогатявана в Infiniting.\n\nБлагодарим ви за съдействието!\n\nПоздрави,\nЕкипът на Infiniting'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [group.author.user.email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return redirect('group-list')

    def get(self, request, pk) :
        return redirect('group-list')