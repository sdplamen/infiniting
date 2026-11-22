from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from groups.models import Group

UserModel = get_user_model()


class GroupListTitleLinkTest(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username='member', password='pw-12345678')
        self.group = Group.objects.create(name='Пейзажи', description='Описание', author=self.user, is_approved=True)
        self.detail_url = reverse('group-detail', kwargs={'pk': self.group.pk})

    def test_name_links_to_group_and_no_view_button(self):
        page = self.client.get(reverse('group-list'))
        self.assertContains(page, f'<a href="{self.detail_url}" class="title-link"')
        self.assertNotContains(page, '>Виж групата<')
        self.assertNotContains(page, 'group-actions')  # logged out: no empty actions row

    def test_join_and_leave_buttons_remain(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('group-list')), 'Присъедини се')
        self.group.members.add(self.user)
        self.assertContains(self.client.get(reverse('group-list')), 'Напусни')


class GroupDetailPageTest(TestCase):
    def setUp(self):
        from photos.models import Photo
        from users.models import Photographer
        self.user = UserModel.objects.create_user(username='member2', password='pw-12345678')
        self.group = Group.objects.create(name='Портрети', author=self.user, is_approved=True)
        author = Photographer.objects.get_or_create(user=self.user)[0]
        self.photo = Photo.objects.create(author=author, image='dummy_image.jpg', caption='Лице', group=self.group)
        self.url = reverse('group-detail', kwargs={'pk': self.group.pk})

    def test_photo_title_links_to_photo(self):
        photo_url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        page = self.client.get(self.url)
        self.assertContains(page, f'<a href="{photo_url}" class="image-link"')
        self.assertNotContains(page, 'onclick="window.location.href')
        self.assertContains(page, f'<a href="{photo_url}" class="title-link"')
        self.assertNotContains(page, 'Виж детайли</a>')

    def test_staff_sees_edit_icon_and_member_sees_leave(self):
        staff = UserModel.objects.create_user(username='staff', password='pw-12345678', is_staff=True)
        self.client.force_login(staff)
        page = self.client.get(self.url)
        self.assertContains(page, 'class="owner-action owner-action-edit"')
        self.assertContains(page, 'Присъедини се')

        member = UserModel.objects.create_user(username='plain-member', password='pw-12345678')
        self.group.members.add(member)
        self.client.force_login(member)
        page = self.client.get(self.url)
        self.assertNotContains(page, 'owner-action-edit')
        self.assertContains(page, 'Напусни групата')


class GroupOwnershipTest(TestCase):
    def setUp(self):
        self.author = UserModel.objects.create_user(username='founder', password='pw-12345678')
        self.member = UserModel.objects.create_user(username='joiner', password='pw-12345678')
        self.staff = UserModel.objects.create_user(username='admin1', password='pw-12345678', is_staff=True)

    def _group(self):
        group = Group.objects.create(name='Улична', author=self.author, is_approved=True)
        group.members.add(self.author, self.member)
        return group

    def test_creating_a_group_sets_author(self):
        self.client.force_login(self.author)
        self.client.post(reverse('group-create'), {'name': 'Нова група', 'description': 'x'})
        group = Group.objects.get(name='Нова група')
        self.assertEqual(group.author, self.author)
        self.assertIn(self.author, group.members.all())

    def test_list_icons_for_author_and_staff_only(self):
        group = self._group()
        edit_url = reverse('group-edit', kwargs={'pk': group.pk})
        for user, visible in ((self.author, True), (self.staff, True), (self.member, False)):
            self.client.force_login(user)
            page = self.client.get(reverse('group-list'))
            (self.assertContains if visible else self.assertNotContains)(page, edit_url)

    def test_edit_and_delete_pages_author_and_staff_only(self):
        group = self._group()
        for name in ('group-edit', 'group-delete'):
            url = reverse(name, kwargs={'pk': group.pk})
            for user, status in ((self.author, 200), (self.staff, 200), (self.member, 403)):
                self.client.force_login(user)
                self.assertEqual(self.client.get(url).status_code, status, (name, user.username))

    def test_group_page_has_delete_icon_for_author(self):
        group = self._group()
        self.client.force_login(self.author)
        page = self.client.get(reverse('group-detail', kwargs={'pk': group.pk}))
        self.assertContains(page, f'href="{reverse("group-delete", kwargs={"pk": group.pk})}" class="owner-action owner-action-delete"')


class GroupPagePhotoIconsTest(TestCase):
    def test_photo_icons_only_for_photo_author(self):
        from photos.models import Photo
        from users.models import Photographer
        owner = UserModel.objects.create_user(username='gowner', password='pw-12345678')
        snapper = UserModel.objects.create_user(username='snapper', password='pw-12345678')
        group = Group.objects.create(name='Макро', author=owner, is_approved=True)
        photo = Photo.objects.create(author=Photographer.objects.get_or_create(user=snapper)[0],
                                     image='dummy_image.jpg', group=group)
        url = reverse('group-detail', kwargs={'pk': group.pk})
        photo_edit = reverse('photo-edit', kwargs={'pk': photo.pk})

        self.client.force_login(snapper)
        page = self.client.get(url)
        self.assertContains(page, f'href="{photo_edit}" class="owner-action owner-action-edit"')
        self.assertContains(page, f'href="{reverse("photo-delete", kwargs={"pk": photo.pk})}" class="owner-action owner-action-delete"')

        self.client.force_login(owner)  # group author, not photo author
        self.assertNotContains(self.client.get(url), photo_edit)


from groups.models import GroupComment
from users.models import Photographer as _Photographer


class GroupCommentsTest(TestCase):
    def setUp(self):
        self.author = UserModel.objects.create_user(username='g-author', password='pw-12345678')
        self.writer = UserModel.objects.create_user(username='g-writer', password='pw-12345678')
        self.stranger = UserModel.objects.create_user(username='g-stranger', password='pw-12345678')
        self.staff = UserModel.objects.create_user(username='g-staff', password='pw-12345678', is_staff=True)
        _Photographer.objects.get_or_create(user=self.writer)
        self.group = Group.objects.create(name='Нощни', author=self.author, is_approved=True)
        self.group.members.add(self.writer)
        self.detail = reverse('group-detail', kwargs={'pk': self.group.pk})

    def _comment(self):
        return GroupComment.objects.create(user=self.writer, group=self.group, text='Здравейте!')

    def _delete_url(self, comment):
        return reverse('group-comment-delete', kwargs={'pk': self.group.pk, 'comment_pk': comment.pk})

    def test_signed_in_user_adds_comment_and_sees_it(self):
        self.client.force_login(self.writer)
        response = self.client.post(reverse('group-comment', kwargs={'pk': self.group.pk}), {'text': 'Първи!'})
        self.assertRedirects(response, self.detail)
        self.assertEqual(GroupComment.objects.get().user, self.writer)
        page = self.client.get(self.detail)
        self.assertContains(page, 'Първи!')
        self.assertContains(page, 'Коментари (1)')

    def test_logged_out_and_empty_are_rejected(self):
        self.client.post(reverse('group-comment', kwargs={'pk': self.group.pk}), {'text': 'x'})
        self.assertContains(self.client.get(self.detail), 'Влезте, за да добавяте коментари')
        self.client.force_login(self.writer)
        self.client.post(reverse('group-comment', kwargs={'pk': self.group.pk}), {'text': ''})
        self.assertFalse(GroupComment.objects.exists())

    def test_non_member_cannot_comment_and_sees_join_hint(self):
        self.client.force_login(self.stranger)
        response = self.client.post(reverse('group-comment', kwargs={'pk': self.group.pk}), {'text': 'Аз не съм член'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(GroupComment.objects.exists())
        page = self.client.get(self.detail)
        self.assertContains(page, 'Присъединете се към групата, за да коментирате.')
        self.assertNotContains(page, reverse('group-comment', kwargs={'pk': self.group.pk}))

    def test_member_sees_comment_form(self):
        self.client.force_login(self.writer)
        self.assertContains(self.client.get(self.detail), f'action="{reverse("group-comment", kwargs={"pk": self.group.pk})}"')

    def test_writer_group_author_and_staff_can_delete(self):
        for user in (self.writer, self.author, self.staff):
            comment = self._comment()
            self.client.force_login(user)
            self.assertRedirects(self.client.post(self._delete_url(comment)), self.detail)
            self.assertFalse(GroupComment.objects.filter(pk=comment.pk).exists())

    def test_others_get_403_and_get_is_refused(self):
        comment = self._comment()
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(self._delete_url(comment)).status_code, 403)
        self.client.force_login(self.writer)
        self.assertEqual(self.client.get(self._delete_url(comment)).status_code, 405)
        self.assertTrue(GroupComment.objects.filter(pk=comment.pk).exists())

    def test_bin_visibility(self):
        comment = self._comment()
        for user, visible in ((self.writer, True), (self.author, True), (self.staff, True), (self.stranger, False)):
            self.client.force_login(user)
            (self.assertContains if visible else self.assertNotContains)(self.client.get(self.detail), self._delete_url(comment))


class GroupApprovalVisibilityTest(TestCase):
    def setUp(self):
        self.author = UserModel.objects.create_user(username='ga-author', password='pw-12345678')
        self.member = UserModel.objects.create_user(username='ga-member', password='pw-12345678')
        self.reader = UserModel.objects.create_user(username='ga-reader', password='pw-12345678')
        self.staff = UserModel.objects.create_user(username='ga-staff', password='pw-12345678', is_staff=True)
        Group.objects.create(name='Видима', author=self.author, is_approved=True)
        self.draft = Group.objects.create(name='Скрита', author=self.author, is_approved=False)
        self.draft.members.add(self.author, self.member)
        self.draft_url = reverse('group-detail', kwargs={'pk': self.draft.pk})

    def test_list_hides_draft_from_visitors_and_others(self):
        for user in (None, self.reader):
            if user:
                self.client.force_login(user)
            page = self.client.get(reverse('group-list'))
            self.assertContains(page, 'Видима')
            self.assertNotContains(page, 'Скрита')

    def test_author_member_and_staff_see_draft_with_badge(self):
        for user in (self.author, self.member, self.staff):
            self.client.force_login(user)
            page = self.client.get(reverse('group-list'))
            self.assertContains(page, 'Скрита')
            self.assertContains(page, 'Чака одобрение', count=1)
            self.assertEqual(self.client.get(self.draft_url).status_code, 200)

    def test_draft_page_and_join_404_for_others(self):
        self.assertEqual(self.client.get(self.draft_url).status_code, 404)
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(self.draft_url).status_code, 404)
        self.assertEqual(self.client.post(reverse('group-join', kwargs={'pk': self.draft.pk})).status_code, 404)
        self.assertNotIn(self.reader, self.draft.members.all())

    def test_member_can_still_leave_draft(self):
        self.client.force_login(self.member)
        self.client.post(reverse('group-leave', kwargs={'pk': self.draft.pk}))
        self.assertNotIn(self.member, self.draft.members.all())

    def test_photo_form_offers_only_visible_groups(self):
        from photos.forms import PhotoUploadForm
        reader_choices = {g.name for g in PhotoUploadForm(user=self.reader).fields['group'].queryset}
        member_choices = {g.name for g in PhotoUploadForm(user=self.member).fields['group'].queryset}
        self.assertEqual(reader_choices, {'Видима'})
        self.assertEqual(member_choices, {'Видима', 'Скрита'})


class GroupJoinTextButtonsTest(TestCase):
    def test_join_and_leave_are_text_buttons_on_all_pages(self):
        from users.models import Photographer
        user = UserModel.objects.create_user(username='joiner2', password='pw-12345678')
        profile = Photographer.objects.get_or_create(user=user)[0]
        group = Group.objects.create(name='Портрет', author=UserModel.objects.create_user(username='gfounder', password='pw-12345678'), is_approved=True)
        self.client.force_login(user)
        join = '<i class="fas fa-plus-circle me-1"></i>Присъедини се'
        for url in (reverse('group-list'), reverse('group-detail', kwargs={'pk': group.pk})):
            self.assertContains(self.client.get(url), f'<button type="submit" class="text-button">{join}</button>', html=True)

        group.members.add(user)
        leave = '<i class="fas fa-sign-out-alt me-1"></i>'
        self.assertContains(self.client.get(reverse('group-list')), f'<button type="submit" class="text-button text-button-danger">{leave}Напусни</button>', html=True)
        self.assertContains(self.client.get(reverse('group-detail', kwargs={'pk': group.pk})), f'<button type="submit" class="text-button text-button-danger">{leave}Напусни групата</button>', html=True)
        self.assertContains(self.client.get(reverse('user-profile-detail', kwargs={'pk': profile.pk})), f'<button type="submit" class="text-button text-button-danger ms-2">{leave}Напусни</button>', html=True)

    def test_leave_on_profile_only_for_the_profile_owner(self):
        from users.models import Photographer
        owner = UserModel.objects.create_user(username='member-x', password='pw-12345678')
        profile = Photographer.objects.get_or_create(user=owner)[0]
        group = Group.objects.create(name='Пейзаж', author=owner, is_approved=True)
        group.members.add(owner)
        self.client.force_login(UserModel.objects.create_user(username='visitor-x', password='pw-12345678'))
        page = self.client.get(reverse('user-profile-detail', kwargs={'pk': profile.pk}))
        self.assertContains(page, 'Пейзаж')
        self.assertNotContains(page, reverse('group-leave', kwargs={'pk': group.pk}))
