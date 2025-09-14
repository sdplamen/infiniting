from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from groups.forms import GroupCreateForm, GroupDetailForm
from groups.mixins import GroupMemberRequiredMixin
from groups.models import Group

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
    paginate_by = 5

    def get_queryset(self):
        return Group.objects.all().order_by('name')

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        max_pages_to_show = 5

        start_page = max(1, page_obj.number - max_pages_to_show)
        end_page = min(paginator.num_pages, start_page + max_pages_to_show + 1)

        if (end_page - start_page + 1) < max_pages_to_show :
            start_page = max(1, end_page - max_pages_to_show + 1)

        context['limited_page_range'] = range(start_page, end_page + 1)

        return context

class GroupDetailView(DetailView):
    model = Group
    template_name = 'groups/group-detail.html'
    context_object_name = 'group'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('-uploaded_at')
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