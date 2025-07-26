from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from articles.models import Article
from users.models import Photographer
from django.core import mail
from django.http import HttpRequest

User = get_user_model()

class TestArticleApproveView(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.approve_url_name = 'article-approve'
        self.article_list_url_name = 'article-list'

    def _create_author_and_article(self, is_approved=False, username_suffix="", email_suffix=""):
        author_user = User.objects.create_user(
            username=f'test_author_user{username_suffix}',
            email=f'test_author_email{email_suffix}@example.com',
            password='authorpassword'
        )

        photographer, created = Photographer.objects.get_or_create(user=author_user)
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article.',
            author=photographer,
            is_approved=is_approved
        )
        return author_user, photographer, article

    def test_article_already_approved_no_email_sent(self):
        author_user, photographer, article = self._create_author_and_article(is_approved=True, username_suffix='_approved', email_suffix='_approved')

        request = HttpRequest()
        request.method = 'POST'
        request.user = self.superuser

        initial_email_count = len(mail.outbox)

        from articles.views import ArticleApproveView
        response = ArticleApproveView().post(request, pk=article.pk)

        article.refresh_from_db()

        self.assertTrue(article.is_approved)
        self.assertEqual(len(mail.outbox), initial_email_count)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.article_list_url_name))

    def test_article_not_approved_email_sent(self):
        author_user, photographer, article = self._create_author_and_article(is_approved=False, username_suffix='_unapproved', email_suffix='_unapproved')

        request = HttpRequest()
        request.method = 'POST'
        request.user = self.superuser

        initial_email_count = len(mail.outbox)

        from articles.views import ArticleApproveView
        response = ArticleApproveView().post(request, pk=article.pk)

        article.refresh_from_db()

        self.assertTrue(article.is_approved)
        self.assertEqual(len(mail.outbox), initial_email_count + 1)
        self.assertEqual(mail.outbox[initial_email_count].to[0], author_user.email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.article_list_url_name))