from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from articles.forms import ArticleForm, ArticleDetailForm
from articles.mixins import ArticleApprovalMixin, AuthorRequiredTestMixin
from articles.models import Article
from users.models import Photographer
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
class ArticleListView(ArticleApprovalMixin, ListView):
    model = Article
    template_name = 'articles/article-list.html'
    context_object_name = 'articles'
    ordering = ['-created_at']
    paginate_by = 5

    # def get_queryset(self):
    #     return Article.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        max_pages_to_show = 1

        start_page = max(1, page_obj.number - max_pages_to_show)
        end_page = min(paginator.num_pages, start_page + max_pages_to_show + 1)

        if (end_page - start_page + 1) < max_pages_to_show :
            start_page = max(1, end_page - max_pages_to_show + 1)

        context['limited_page_range'] = range(start_page, end_page)

        return context

class ArticleDetailView(ArticleApprovalMixin, DetailView):
    model = Article
    template_name = 'articles/article-detail.html'
    context_object_name = 'article'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ArticleDetailForm(article=self.object, user=self.request.user)
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
