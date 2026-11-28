from django.db.models import Count
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from groups.forms import GroupCreateForm, GroupDetailForm, GroupCommentForm
from groups.mixins import GroupOwnerOrStaffRequiredMixin, GroupApprovalMixin
from groups.models import Group, GroupComment
from users.mixins import PaginationMixin


# Create your views here.
class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'groups/group-create.html'
    success_url = reverse_lazy('group-list')

    def form_valid(self, form):
        form.instance.author = self.request.user  # required field; the form doesn't include it
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        return response


class GroupListView(GroupApprovalMixin, ListView):
    model = Group
    template_name = 'groups/group-list.html'
    context_object_name = 'groups'
    paginate_by = 5

    def get_queryset(self):
        return super().get_queryset().annotate(member_count=Count('members')).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # join/leave buttons: one query for the viewer's groups, not a member list per group
        user = self.request.user
        context['my_group_ids'] = (
            set(user.user_groups.values_list('pk', flat=True)) if user.is_authenticated else set())
        return context

class GroupDetailView(GroupApprovalMixin, PaginationMixin, DetailView):
    model = Group
    template_name = 'groups/group-detail.html'
    context_object_name = 'group'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photos = self.object.photos.for_cards().order_by('-uploaded_at', '-pk')
        pagination_data = self.get_paginated_queryset(photos, self.request)
        context.update(pagination_data)
        context['photos'] = context['page_obj']
        context['form'] = GroupDetailForm(group=self.object, user=self.request.user)
        context['comments'] = self.object.comments.select_related('user__photographer')
        context['comment_form'] = GroupCommentForm()
        return context

class GroupUpdateView(LoginRequiredMixin, GroupOwnerOrStaffRequiredMixin, UpdateView):
    model = Group
    form_class = GroupCreateForm
    template_name = 'groups/group-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('group-detail', kwargs={'pk': self.object.pk})

class GroupDeleteView(LoginRequiredMixin, GroupOwnerOrStaffRequiredMixin, DeleteView):
    model = Group
    template_name = 'groups/group-delete.html'
    success_url = reverse_lazy('group-list')  # Corrected

def _handle_group_membership_change(request, pk, action_type):
    # joining needs a group the user can see; leaving works for any group they are in
    groups = Group.visible_to(request.user) if action_type == 'add' else Group.objects.all()
    group = get_object_or_404(groups, pk=pk)

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
            recipient_list = [group.author.email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return redirect('group-list')

    def get(self, request, pk) :
        return redirect('group-list')


@login_required
@require_POST
def add_group_comment(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if not group.members.filter(pk=request.user.pk).exists():
        raise PermissionDenied  # only members take part in a group's discussion
    form = GroupCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.group = group
        comment.save()
    return redirect('group-detail', pk=pk)


@login_required
@require_POST
def delete_group_comment(request, pk, comment_pk):
    """The comment's writer, the group's author or staff may delete a comment."""
    comment = get_object_or_404(GroupComment.objects.select_related('group'), pk=comment_pk, group_id=pk)
    user = request.user
    if not (user.is_staff or user.id in (comment.user_id, comment.group.author_id)):
        raise PermissionDenied
    comment.delete()
    return redirect('group-detail', pk=pk)
