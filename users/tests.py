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


class ProfileListTitleLinkTest(TestCase):
    def test_username_links_to_profile_and_no_view_button(self):
        profile = Photographer.objects.get_or_create(
            user=UserModel.objects.create_user(username='ivana', password='pw-12345678'))[0]
        detail_url = reverse('user-profile-detail', kwargs={'pk': profile.pk})

        page = self.client.get(reverse('user-profile-list'))
        self.assertContains(page, f'<a href="{detail_url}" class="title-link" title="Виж профила">ivana</a>', html=True)
        self.assertNotContains(page, 'Виж профила.</a>')

    def test_signed_in_user_can_follow_from_list(self):
        target = Photographer.objects.get_or_create(
            user=UserModel.objects.create_user(username='target', password='pw-12345678'))[0]
        viewer = UserModel.objects.create_user(username='viewer', password='pw-12345678')
        self.client.force_login(viewer)
        page = self.client.get(reverse('user-profile-list'))
        follow_url = reverse('user-follow', kwargs={'pk': target.user.pk})
        self.assertContains(page, f'action="{follow_url}"')

        self.client.post(follow_url)
        page = self.client.get(reverse('user-profile-list'))
        self.assertContains(page, f'action="{reverse("user-unfollow", kwargs={"pk": target.user.pk})}"')



class ProfileDetailLinksTest(TestCase):
    def setUp(self):
        from articles.models import Article
        from photos.models import Photo
        self.owner = UserModel.objects.create_user(username='artist', password='pw-12345678')
        self.profile = Photographer.objects.get_or_create(user=self.owner)[0]
        self.photo = Photo.objects.create(author=self.profile, image='dummy_image.jpg', caption='Кула')
        self.article = Article.objects.create(title='Композиция', content='текст', author=self.profile, is_approved=True)
        self.url = reverse('user-profile-detail', kwargs={'pk': self.profile.pk})

    def test_photo_and_article_links(self):
        page = self.client.get(self.url)
        photo_url = reverse('photo-detail', kwargs={'pk': self.photo.pk})
        self.assertContains(page, f'<a href="{photo_url}" class="image-link"')
        self.assertContains(page, f'<a href="{photo_url}" class="title-link"')
        self.assertContains(page, f'<a href="{reverse("article-detail", kwargs={"pk": self.article.pk})}" class="title-link"')
        self.assertNotContains(page, 'alt={{')

    def test_follow_button(self):
        self.client.force_login(UserModel.objects.create_user(username='fan', password='pw-12345678'))
        page = self.client.get(self.url)
        self.assertContains(page, '>Последвай</button>')
        self.assertNotContains(page, 'Последвай.')


class ProfileListOwnerIconsTest(TestCase):
    """Profile edit/delete icons live only on the profile page, not on profile cards."""
    def test_no_icons_on_own_card_but_on_profile_page(self):
        me = UserModel.objects.create_user(username='self', password='pw-12345678')
        mine = Photographer.objects.get_or_create(user=me)[0]
        edit_url = reverse("user-profile-edit", kwargs={"pk": mine.pk})
        self.client.force_login(me)
        page = self.client.get(reverse('user-profile-list'))
        self.assertNotContains(page, f'href="{edit_url}"')
        self.assertNotContains(page, 'owner-action')
        self.assertNotContains(page, f'action="{reverse("user-follow", kwargs={"pk": me.pk})}"')  # still no follow on own card
        detail = self.client.get(reverse('user-profile-detail', kwargs={'pk': mine.pk}))
        self.assertContains(detail, f'href="{edit_url}" class="owner-action owner-action-edit"')

class ProfilePageContentIconsTest(TestCase):
    def test_no_photo_or_article_icons_on_profile_page(self):
        from articles.models import Article
        from photos.models import Photo
        owner = UserModel.objects.create_user(username='owner3', password='pw-12345678')
        profile = Photographer.objects.get_or_create(user=owner)[0]
        photo = Photo.objects.create(author=profile, image='dummy_image.jpg')
        article = Article.objects.create(title='А', content='б', author=profile, is_approved=True)
        url = reverse('user-profile-detail', kwargs={'pk': profile.pk})
        links = [reverse('photo-edit', kwargs={'pk': photo.pk}), reverse('photo-delete', kwargs={'pk': photo.pk}),
                 reverse('article-edit', kwargs={'pk': article.pk}), reverse('article-delete', kwargs={'pk': article.pk})]

        self.client.force_login(owner)
        page = self.client.get(url)
        for link in links:  # photo and article icons live only on their own pages
            self.assertNotContains(page, f'href="{link}"')

        self.client.force_login(UserModel.objects.create_user(username='visitor', password='pw-12345678'))
        page = self.client.get(url)
        for link in links:
            self.assertNotContains(page, link)


from users.models import ProfileComment, Follow


class ProfileCommentsTest(TestCase):
    def setUp(self):
        self.owner = UserModel.objects.create_user(username='pr-owner', password='pw-12345678')
        self.writer = UserModel.objects.create_user(username='pr-writer', password='pw-12345678')
        self.stranger = UserModel.objects.create_user(username='pr-stranger', password='pw-12345678')
        Photographer.objects.get_or_create(user=self.writer)
        self.profile = Photographer.objects.get_or_create(user=self.owner)[0]
        Follow.objects.create(follower=self.writer, followed=self.owner)
        self.detail = reverse('user-profile-detail', kwargs={'pk': self.profile.pk})
        self.comment_url = reverse('user-profile-comment', kwargs={'pk': self.profile.pk})

    def _comment(self):
        return ProfileComment.objects.create(user=self.writer, photographer=self.profile, text='Страхотно портфолио!')

    def _delete_url(self, comment):
        return reverse('user-profile-comment-delete', kwargs={'pk': self.profile.pk, 'comment_pk': comment.pk})

    def test_signed_in_user_adds_comment_and_sees_it(self):
        self.client.force_login(self.writer)
        response = self.client.post(reverse('user-profile-comment', kwargs={'pk': self.profile.pk}), {'text': 'Браво'})
        self.assertRedirects(response, self.detail)
        self.assertEqual(ProfileComment.objects.get().user, self.writer)
        page = self.client.get(self.detail)
        self.assertContains(page, 'Браво')
        self.assertContains(page, 'Коментари (1)')

    def test_logged_out_and_empty_are_rejected(self):
        self.client.post(reverse('user-profile-comment', kwargs={'pk': self.profile.pk}), {'text': 'x'})
        self.assertContains(self.client.get(self.detail), 'Влезте, за да добавяте коментари')
        self.client.force_login(self.writer)
        self.client.post(reverse('user-profile-comment', kwargs={'pk': self.profile.pk}), {'text': ''})
        self.assertFalse(ProfileComment.objects.exists())

    def test_owner_can_reply_on_own_profile(self):
        self.client.force_login(self.owner)
        self.client.post(self.comment_url, {'text': 'Благодаря!'})
        self.assertEqual(ProfileComment.objects.get().user, self.owner)

    def test_non_follower_cannot_comment_and_sees_follow_hint(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(self.comment_url, {'text': 'Здрасти'}).status_code, 403)
        self.assertFalse(ProfileComment.objects.exists())
        page = self.client.get(self.detail)
        self.assertContains(page, 'Последвайте този фотограф, за да коментирате.')
        self.assertNotContains(page, f'action="{self.comment_url}"')

    def test_writer_and_profile_owner_can_delete(self):
        for user in (self.writer, self.owner):
            comment = self._comment()
            self.client.force_login(user)
            self.assertRedirects(self.client.post(self._delete_url(comment)), self.detail)
            self.assertFalse(ProfileComment.objects.filter(pk=comment.pk).exists())

    def test_others_get_403_and_get_is_refused(self):
        comment = self._comment()
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(self._delete_url(comment)).status_code, 403)
        self.client.force_login(self.writer)
        self.assertEqual(self.client.get(self._delete_url(comment)).status_code, 405)
        self.assertTrue(ProfileComment.objects.filter(pk=comment.pk).exists())

    def test_bin_visibility(self):
        comment = self._comment()
        for user, visible in ((self.writer, True), (self.owner, True), (self.stranger, False)):
            self.client.force_login(user)
            (self.assertContains if visible else self.assertNotContains)(self.client.get(self.detail), self._delete_url(comment))


class FollowTextButtonsTest(TestCase):
    def test_follow_and_unfollow_are_text_buttons_on_both_pages(self):
        target = Photographer.objects.get_or_create(user=UserModel.objects.create_user(username='star', password='pw-12345678'))[0]
        fan = UserModel.objects.create_user(username='fan2', password='pw-12345678')
        self.client.force_login(fan)
        pages = (reverse('user-profile-list'), reverse('user-profile-detail', kwargs={'pk': target.pk}))
        for url in pages:
            page = self.client.get(url)
            self.assertContains(page, '<button type="submit" class="text-button"><i class="fas fa-user-plus me-1"></i>Последвай</button>', html=True)
        self.client.post(reverse('user-follow', kwargs={'pk': target.user.pk}))
        for url in pages:
            page = self.client.get(url)
            self.assertContains(page, '<button type="submit" class="text-button text-button-danger"><i class="fas fa-user-minus me-1"></i>Не следвай</button>', html=True)
            self.assertNotContains(page, 'custom-button-small">Не следвай')


class AuthPageButtonsTest(TestCase):
    def test_sign_in_and_sign_up_are_text_buttons_and_still_work(self):
        page = self.client.get(reverse('login'))
        self.assertContains(page, '<button type="submit" class="text-button text-button-success"><i class="fas fa-sign-in-alt me-1"></i>Вход</button>', html=True)
        page = self.client.get(reverse('register'))
        self.assertContains(page, '<button type="submit" class="text-button text-button-success"><i class="fas fa-user-plus me-1"></i>Регистрация</button>', html=True)
        UserModel.objects.create_user(username='signin', password='pw-12345678')
        response = self.client.post(reverse('login'), {'username': 'signin', 'password': 'pw-12345678'})
        self.assertEqual(response.status_code, 302)


class NavBarProfilesLinkTest(TestCase):
    def test_nav_bar_links_to_profiles_list_for_everyone(self):
        link = f'<a href="{reverse("user-profile-list")}" title="Профили"><i class="bi bi-person-lines-fill"></i></a>'
        self.assertContains(self.client.get(reverse('photo-home')), link, html=True)
        self.client.force_login(UserModel.objects.create_user(username='navuser', password='pw-12345678'))
        self.assertContains(self.client.get(reverse('article-list')), link, html=True)
