from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q


class ArticleApprovalMixin:
    """Unapproved articles are visible only to approvers and to their own author."""
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.has_perm('articles.can_approve_articles'):
            visible = Q(is_approved=True)
            if user.is_authenticated:
                visible |= Q(author__user=user)
            queryset = queryset.filter(visible)
        return queryset

class AuthorRequiredTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().author.user

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