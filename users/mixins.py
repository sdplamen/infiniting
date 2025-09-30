from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator


class UserIsProfileOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().user


class PaginationMixin:
    max_pages_to_show = 3

    def get_paginated_queryset(self, queryset, request):
        paginator = Paginator(queryset, self.paginate_by)
        page = request.GET.get('page')

        # try:
        #     page_obj = paginator.page(page)
        # except PageNotAnInteger:
        #     page_obj = paginator.page(1)
        # except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

        return {
            'paginator': paginator,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
        }

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
