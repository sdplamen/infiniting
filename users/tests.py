from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import Photographer

UserModel = get_user_model()


class ProfileOwnerActionsTest(TestCase):
    def setUp(self):
        self.owner = UserModel.objects.create_user(username='owner', password='pw-12345678')
        self.profile = Photographer.objects.get_or_create(user=self.owner)[0]
        self.url = reverse('user-profile-detail', kwargs={'pk': self.profile.pk})

    def test_owner_sees_icon_buttons(self):
        self.client.force_login(self.owner)
        page = self.client.get(self.url)
        self.assertContains(page, 'class="owner-action owner-action-edit"')
        self.assertContains(page, 'class="owner-action owner-action-delete"')
        self.assertContains(page, f'href="{reverse("user-profile-edit", kwargs={"pk": self.profile.pk})}"')
        self.assertContains(page, f'href="{reverse("user-profile-delete", kwargs={"pk": self.profile.pk})}"')

    def test_other_user_does_not(self):
        other = UserModel.objects.create_user(username='other', password='pw-12345678')
        self.client.force_login(other)
        self.assertNotContains(self.client.get(self.url), 'owner-action')
