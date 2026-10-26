from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator


class UserIsProfileOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().user


class PaginationMixin:
    paginate_by = 10
    max_pages_to_show = 3

    def get_paginated_queryset(self, queryset, request):
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        start_page = max(1, page_obj.number - self.max_pages_to_show)
        end_page = min(paginator.num_pages, start_page + self.max_pages_to_show * 2)

        if (end_page - start_page + 1) <= self.max_pages_to_show * 2:
            start_page = max(1, end_page - self.max_pages_to_show * 2)

        return {
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
            'paginator': paginator,
            'limited_page_range': range(start_page, end_page + 1),
        }