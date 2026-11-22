from django.contrib.auth.mixins import UserPassesTestMixin


class GroupApprovalMixin:
    """Hide unapproved groups from everyone but staff (the approvers), the author and members."""
    def get_queryset(self):
        from groups.models import Group
        return super().get_queryset().filter(pk__in=Group.visible_to(self.request.user).values('pk'))

class GroupMemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user in self.get_object().members.all()

class PaginationMixin:
    max_pages_to_show = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page_obj = context.get('page_obj')

        if not paginator or not page_obj:
            return context

        start_page = max(1, page_obj.number - self.max_pages_to_show)
        end_page = min(paginator.num_pages, start_page + self.max_pages_to_show * 2)

        if (end_page - start_page + 1) <= self.max_pages_to_show * 2:
            start_page = max(1, end_page - self.max_pages_to_show * 2)

        context['limited_page_range'] = range(start_page, end_page + 1)
        return context

class GroupOwnerOrStaffRequiredMixin(UserPassesTestMixin):
    """Only the group's author or staff may edit or delete it."""
    def test_func(self):
        user = self.request.user
        return user.is_staff or self.get_object().author_id == user.id
