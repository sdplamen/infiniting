from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from articles.forms import ArticleForm, ArticleDetailForm, ArticleCommentForm
from articles.mixins import ArticleApprovalMixin, AuthorRequiredTestMixin
from articles.models import Article, ArticleComment
from users.models import Photographer
from django.core.mail import send_mail
from django.conf import settings
from users.mixins import PaginationMixin


# Create your views here.
class ArticleListView(ArticleApprovalMixin, PaginationMixin, ListView):
    model = Article
    template_name = 'articles/article-list.html'
    context_object_name = 'articles'
    ordering = ['-created_at']
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        pagination_data = self.get_paginated_queryset(queryset, self.request)
        context.update(pagination_data)
        return context

class ArticleDetailView(ArticleApprovalMixin, DetailView):
    model = Article
    template_name = 'articles/article-detail.html'
    context_object_name = 'article'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ArticleDetailForm(article=self.object, user=self.request.user)
        context['comments'] = self.object.comments.select_related('user__photographer')
        context['comment_form'] = ArticleCommentForm()
        return context

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article-create.html'
    success_url = reverse_lazy('article-list')

    def form_valid(self, form):
        try:
            photographer = self.request.user.photographer
        except Photographer.DoesNotExist:
            form.add_error(None, 'You need a photographer profile to write articles.')
            return self.form_invalid(form)
        form.instance.author = photographer
        return super().form_valid(form)

class ArticleUpdateView(LoginRequiredMixin, AuthorRequiredTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('article-detail', kwargs={'pk': self.object.pk})

class ArticleDeleteView(LoginRequiredMixin, AuthorRequiredTestMixin, DeleteView):
    model = Article
    template_name = 'articles/article-delete.html'
    success_url = reverse_lazy('article-list')
    pk_url_kwarg = 'pk'

class ArticleApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        if not article.is_approved:
            article.is_approved = True
            article.save()
            subject = f'Вашата статия {article.title} беше одобрена за четене!'
            message = f'Скъпи {article.author.user.username},\n\nВашата статия {article.title} беше одобрена и вече може да бъде прочетена в Infiniting.\n\nБлагодарим ви за съдействието!\n\nПоздрави,\nЕкипът на Infiniting'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [article.author.user.email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return redirect('article-list')

    def get(self, request, pk) :
        return redirect('article-list')


@login_required
@require_POST
def add_article_comment(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_approved:
        raise PermissionDenied  # comments open once the article is approved
    form = ArticleCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.article = article
        comment.save()
    return redirect('article-detail', pk=pk)


@login_required
@require_POST
def delete_article_comment(request, pk, comment_pk):
    """The comment's writer or the article's author may delete a comment."""
    comment = get_object_or_404(ArticleComment.objects.select_related('article__author'), pk=comment_pk, article_id=pk)
    if request.user.id not in (comment.user_id, comment.article.author.user_id):
        raise PermissionDenied
    comment.delete()
    return redirect('article-detail', pk=pk)
