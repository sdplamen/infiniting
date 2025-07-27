from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.http import HttpRequest
from django.conf import settings
from articles.models import Article, Photographer
from articles.views import ArticleApproveView

User = get_user_model()

class TestArticleApproveView(TestCase):
    def setUp(self):
        self._original_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.article_list_url_name = 'article-list'

    def tearDown(self):
        settings.EMAIL_BACKEND = self._original_email_backend
        mail.outbox = []

    def _create_author_and_article(self, is_approved=False, username='', email=''):
        author_user = User.objects.create_user(
            username=f'test_author_user{username}',
            email=f'test_author_email{email}@example.com',
            password='authorpassword'
        )

        photographer, created = Photographer.objects.get_or_create(user=author_user)
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article.',
            author=photographer,
            is_approved=is_approved
        )
        return author_user, article

    def _test_article_approval_scenario(self, initial_approval_status, expected_email_sent):
        mail.outbox = []

        suffix = '_approved' if initial_approval_status else '_unapproved'
        author_user, article = self._create_author_and_article(
            is_approved=initial_approval_status,
            username=suffix,
            email=suffix
        )

        request = HttpRequest()
        request.method = 'POST'
        request.user = self.superuser

        initial_email_count = len(mail.outbox)

        response = ArticleApproveView().post(request, pk=article.pk)

        article.refresh_from_db()

        self.assertTrue(article.is_approved)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(self.article_list_url_name))

        if expected_email_sent:
            self.assertEqual(len(mail.outbox), initial_email_count + 1)
            self.assertEqual(mail.outbox[initial_email_count].to[0], author_user.email)
        else:
            self.assertEqual(len(mail.outbox), initial_email_count)

    def test_article_already_approved(self):
        self._test_article_approval_scenario(initial_approval_status=True, expected_email_sent=False)

    def test_article_not_approved(self):
        self._test_article_approval_scenario(initial_approval_status=False, expected_email_sent=True)