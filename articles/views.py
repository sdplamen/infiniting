from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from .forms import ArticleForm
from .models import Article
from users.models import Photographer

# Create your views here.
class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article-list.html'
    context_object_name = 'articles'
    ordering = ['-created_at']
    paginate_by = 10

    def get_queryset(self) :
        queryset = super().get_queryset()
        if not self.request.user.has_perm('articles.can_approve_articles') :
            queryset = queryset.filter(is_approved=True)
        return queryset

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article-detail.html'
    context_object_name = 'article'
    pk_url_kwarg = 'pk'

    def get_queryset(self) :
        queryset = super().get_queryset()
        if not self.request.user.has_perm('articles.can_approve_articles') :
            queryset = queryset.filter(is_approved=True)
        return queryset

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

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article-edit.html'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse('article-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        return self.request.user == self.get_object().author.user

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'articles/article-delete.html'
    success_url = reverse_lazy('article-list')
    pk_url_kwarg = 'pk'

    def test_func(self):
        return self.request.user == self.get_object().author.user

    def test_func(self):
        return self.request.user == self.get_object().author.user

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'articles/article-delete.html'
    success_url = reverse_lazy('article-list')
    pk_url_kwarg = 'pk'

    def test_func(self):
        return self.request.user == self.get_object().author.user

class ArticleApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        if not article.is_approved:
            article.is_approved = True
            article.save()
        return redirect('article-list')

    def get(self, request, pk) :
        return redirect('article-list')
