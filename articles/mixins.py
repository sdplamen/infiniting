from django.contrib.auth.mixins import UserPassesTestMixin


class ArticleApprovalMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('articles.can_approve_articles'):
            queryset = queryset.filter(is_approved=True)
        return queryset

class AuthorRequiredTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().author.user