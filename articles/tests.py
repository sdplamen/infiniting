from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from articles.models import Article, Photographer

UserModel = get_user_model()

class TestApproveArticle(TestCase):
    def setUp(self):
        self.user_credentials = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'strong-password-123',
        }

        self.user = UserModel.objects.create_user(
            username=self.user_credentials['username'],
            email=self.user_credentials['email'],
            password=self.user_credentials['password'],
            is_staff=True,
            is_superuser=True,
        )
        # self.user = UserModel.objects.create_superuser(
        #     **self.user_credentials
        # )

        self.photographer, created = Photographer.objects.get_or_create(
            user=self.user,
            defaults={
            }
        )

        self.article = Article.objects.create(
            title='Test Article',
            content="This is some test content.",
            is_approved=False,
            author=self.photographer,
        )

        logged_in = self.client.login(
            username=self.user_credentials['username'],
            password=self.user_credentials['password']
        )
        self.assertTrue(logged_in, "Client failed to log in")

    def test__approve_valid_article__approves_the_article_and_redirects(self):
        # Act
        response = self.client.post(
            reverse('article-approve', args=[self.article.pk]),
            HTTP_REFERER=reverse('article-list')
        )

        self.article.refresh_from_db()

        # Assert
        self.assertRedirects(response, reverse('article-list'))
        self.assertTrue(self.article.is_approved)

    def test__approve_invalid_article__raises_DoesNotExist_error(self):
        response = self.client.post(
            reverse('article-approve', args=[99999999]),
            HTTP_REFERER=reverse('article-list')
        )

        self.assertEqual(response.status_code, 404)

class ArticleListTitleLinkTest(TestCase):
    def test_title_opens_full_article_and_no_read_more_button(self):
        author = Photographer.objects.get_or_create(
            user=UserModel.objects.create_user(username='writer', password='pw-12345678'))[0]
        words = ' '.join(f'word{i}' for i in range(30))
        article = Article.objects.create(title='Светлина', content=words, author=author, is_approved=True)
        detail_url = reverse('article-detail', kwargs={'pk': article.pk})

        page = self.client.get(reverse('article-list'))
        self.assertContains(page, f'<a href="{detail_url}" class="title-link"')
        self.assertNotContains(page, 'Прочети повече')
        self.assertNotContains(page, 'word29')  # list still shows a short excerpt

        self.assertContains(self.client.get(detail_url), 'word29')  # title leads to the full text


class ArticleDetailActionsTest(TestCase):
    def setUp(self):
        self.writer = UserModel.objects.create_user(username='writer2', password='pw-12345678')
        author = Photographer.objects.get_or_create(user=self.writer)[0]
        self.article = Article.objects.create(title='Т', content='текст', author=author, is_approved=True)
        self.url = reverse('article-detail', kwargs={'pk': self.article.pk})

    def test_author_sees_icon_buttons(self):
        self.client.force_login(self.writer)
        page = self.client.get(self.url)
        self.assertContains(page, f'<a href="{reverse("article-edit", kwargs={"pk": self.article.pk})}" class="owner-action owner-action-edit"')
        self.assertContains(page, f'<a href="{reverse("article-delete", kwargs={"pk": self.article.pk})}" class="owner-action owner-action-delete"')

    def test_other_user_sees_no_actions_row(self):
        self.client.force_login(UserModel.objects.create_user(username='reader', password='pw-12345678'))
        self.assertNotContains(self.client.get(self.url), 'detail-actions')


class ArticleListOwnerIconsTest(TestCase):
    def setUp(self):
        self.me = UserModel.objects.create_user(username='me', password='pw-12345678')
        other = UserModel.objects.create_user(username='someone', password='pw-12345678')
        self.mine = Article.objects.create(title='Моя', content='а', is_approved=True,
                                           author=Photographer.objects.get_or_create(user=self.me)[0])
        self.theirs = Article.objects.create(title='Чужда', content='б', is_approved=True,
                                             author=Photographer.objects.get_or_create(user=other)[0])

    def test_no_icons_on_list_cards_but_on_article_page(self):
        self.client.force_login(self.me)
        edit_url = reverse("article-edit", kwargs={"pk": self.mine.pk})
        page = self.client.get(reverse('article-list'))
        self.assertNotContains(page, f'href="{edit_url}"')
        self.assertNotContains(page, 'card-owner-actions')
        detail = self.client.get(reverse('article-detail', kwargs={'pk': self.mine.pk}))
        self.assertContains(detail, f'href="{edit_url}" class="owner-action owner-action-edit"')

    def test_logged_out_sees_no_icons(self):
        self.assertNotContains(self.client.get(reverse('article-list')), 'owner-action')


from articles.models import ArticleComment


class ArticleCommentsTest(TestCase):
    def setUp(self):
        self.author = UserModel.objects.create_user(username='a-author', password='pw-12345678')
        self.writer = UserModel.objects.create_user(username='a-writer', password='pw-12345678')
        self.stranger = UserModel.objects.create_user(username='a-stranger', password='pw-12345678')
        Photographer.objects.get_or_create(user=self.writer)
        self.article = Article.objects.create(title='Т', content='с', is_approved=True,
                                              author=Photographer.objects.get_or_create(user=self.author)[0])
        self.detail = reverse('article-detail', kwargs={'pk': self.article.pk})

    def _comment(self):
        return ArticleComment.objects.create(user=self.writer, article=self.article, text='Браво!')

    def _delete_url(self, comment):
        return reverse('article-comment-delete', kwargs={'pk': self.article.pk, 'comment_pk': comment.pk})

    def test_signed_in_user_adds_comment_and_sees_it(self):
        self.client.force_login(self.writer)
        response = self.client.post(reverse('article-comment', kwargs={'pk': self.article.pk}), {'text': 'Чудесно'})
        self.assertRedirects(response, self.detail)
        comment = ArticleComment.objects.get()
        self.assertEqual((comment.user, comment.text), (self.writer, 'Чудесно'))
        page = self.client.get(self.detail)
        self.assertContains(page, 'Чудесно')
        self.assertContains(page, 'Коментари (1)')

    def test_logged_out_cannot_add_and_sees_login_link(self):
        self.client.post(reverse('article-comment', kwargs={'pk': self.article.pk}), {'text': 'x'})
        self.assertFalse(ArticleComment.objects.exists())
        self.assertContains(self.client.get(self.detail), 'Влезте, за да добавяте коментари')

    def test_empty_comment_is_ignored(self):
        self.client.force_login(self.writer)
        self.client.post(reverse('article-comment', kwargs={'pk': self.article.pk}), {'text': ''})
        self.assertFalse(ArticleComment.objects.exists())

    def test_unapproved_article_does_not_take_comments(self):
        Article.objects.filter(pk=self.article.pk).update(is_approved=False)
        comment_url = reverse('article-comment', kwargs={'pk': self.article.pk})
        self.client.force_login(self.writer)  # regular user: draft page is hidden, posting refused
        self.assertEqual(self.client.post(comment_url, {'text': 'Рано'}).status_code, 403)
        self.assertEqual(self.client.get(self.detail).status_code, 404)

        self.client.force_login(self.author)  # author sees the draft with comments closed
        self.assertEqual(self.client.post(comment_url, {'text': 'Рано'}).status_code, 403)
        page = self.client.get(self.detail)
        self.assertContains(page, 'Коментарите ще бъдат отворени след одобрение на статията.')
        self.assertNotContains(page, f'action="{comment_url}"')
        self.assertFalse(ArticleComment.objects.exists())

    def test_writer_and_article_author_can_delete(self):
        for user in (self.writer, self.author):
            comment = self._comment()
            self.client.force_login(user)
            self.assertRedirects(self.client.post(self._delete_url(comment)), self.detail)
            self.assertFalse(ArticleComment.objects.filter(pk=comment.pk).exists())

    def test_others_get_403_and_get_is_refused(self):
        comment = self._comment()
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(self._delete_url(comment)).status_code, 403)
        self.client.force_login(self.writer)
        self.assertEqual(self.client.get(self._delete_url(comment)).status_code, 405)
        self.assertTrue(ArticleComment.objects.filter(pk=comment.pk).exists())

    def test_bin_shown_to_writer_and_author_only(self):
        comment = self._comment()
        for user, visible in ((self.writer, True), (self.author, True), (self.stranger, False)):
            self.client.force_login(user)
            (self.assertContains if visible else self.assertNotContains)(self.client.get(self.detail), self._delete_url(comment))


class ArticleListApprovalTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Permission
        self.author = UserModel.objects.create_user(username='draft-author', password='pw-12345678')
        self.reader = UserModel.objects.create_user(username='draft-reader', password='pw-12345678')
        self.approver = UserModel.objects.create_user(username='approver', password='pw-12345678')
        self.approver.user_permissions.add(Permission.objects.get(codename='can_approve_articles'))
        author = Photographer.objects.get_or_create(user=self.author)[0]
        Article.objects.create(title='Одобрена', content='а', author=author, is_approved=True)
        Article.objects.create(title='Чернова', content='б', author=author, is_approved=False)
        self.url = reverse('article-list')

    def test_draft_hidden_from_visitors_and_other_users(self):
        for user in (None, self.reader):
            if user:
                self.client.force_login(user)
            page = self.client.get(self.url)
            self.assertContains(page, 'Одобрена')
            self.assertNotContains(page, 'Чернова')

    def test_author_and_approver_see_draft_with_badge(self):
        for user in (self.author, self.approver):
            self.client.force_login(user)
            page = self.client.get(self.url)
            self.assertContains(page, 'Чернова')
            self.assertContains(page, 'Чака одобрение', count=1)

    def test_draft_page_404_for_others_open_for_author_and_approver(self):
        draft = Article.objects.get(title='Чернова')
        url = reverse('article-detail', kwargs={'pk': draft.pk})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(url).status_code, 404)
        for user in (self.author, self.approver):
            self.client.force_login(user)
            self.assertContains(self.client.get(url), 'Чернова')

    def test_profile_page_lists_drafts_only_for_author(self):
        profile_url = reverse('user-profile-detail', kwargs={'pk': self.author.photographer.pk})
        self.client.force_login(self.reader)
        page = self.client.get(profile_url)
        self.assertContains(page, 'Одобрена')
        self.assertNotContains(page, 'Чернова')
        self.client.force_login(self.author)
        self.assertContains(self.client.get(profile_url), 'Чернова')


class ApproveTextButtonsTest(TestCase):
    def test_approve_buttons_are_text_buttons(self):
        from groups.models import Group
        staff = UserModel.objects.create_user(username='appr', password='pw-12345678', is_staff=True, is_superuser=True)
        author = Photographer.objects.get_or_create(user=staff)[0]
        article = Article.objects.create(title='т', content='с', author=author, is_approved=False)
        group = Group.objects.create(name='Чакаща', author=staff, is_approved=False)
        self.client.force_login(staff)
        icon = '<i class="fas fa-check-circle me-1"></i>'
        self.assertContains(self.client.get(reverse('article-detail', kwargs={'pk': article.pk})),
                            f'<button type="submit" class="text-button text-button-success">{icon}Потвърди статията</button>', html=True)
        self.assertContains(self.client.get(reverse('group-detail', kwargs={'pk': group.pk})),
                            f'<button type="submit" class="text-button text-button-success">{icon}Потвърди групата</button>', html=True)


class ArticleCardAuthorChipTest(TestCase):
    def test_author_chip_and_no_publish_date_on_cards(self):
        user = UserModel.objects.create_user(username='chip', password='pw-12345678')
        profile = Photographer.objects.get_or_create(user=user)[0]
        Article.objects.create(title='Т', content='с', author=profile, is_approved=True)
        page = self.client.get(reverse('article-list'))
        self.assertContains(page, f'<a href="{reverse("user-profile-detail", kwargs={"pk": profile.pk})}" class="author-chip" title="Автор">'
                                  '<i class="fas fa-user-edit me-1"></i>chip</a>', html=True)
        self.assertNotContains(page, 'Публикувано на')
        self.assertNotContains(page, 'Автор: <a')
