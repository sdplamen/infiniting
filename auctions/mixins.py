from django.contrib.auth.mixins import UserPassesTestMixin, AccessMixin


class StaffOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

class StaffOrSuperuserRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff and not request.user.is_superuser:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

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