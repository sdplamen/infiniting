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
        self.assertContains(page, f'<a href="{detail_url}" class="article-title-link"')
        self.assertNotContains(page, 'Прочети повече')
        self.assertNotContains(page, 'word29')  # list still shows a short excerpt

        self.assertContains(self.client.get(detail_url), 'word29')  # title leads to the full text
