from django.contrib.auth.mixins import UserPassesTestMixin


class GroupMemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user in self.get_object().members.all()