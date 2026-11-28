from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from essays.forms import AddPhotosForm, EssayForm
from essays.models import Essay, EssayItem
from users.models import Photographer


class EssayOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only the essay's author may change it."""
    model = Essay

    def get_queryset(self):
        return Essay.objects.select_related('author__user')

    def test_func(self):
        return self.get_object().is_owned_by(self.request.user)


class EssayListView(ListView):
    template_name = 'essays/essay-list.html'
    context_object_name = 'essays'
    paginate_by = 9

    def get_queryset(self):
        return (Essay.objects.filter(is_published=True)
                .select_related('author__user', 'cover_photo')
                .annotate(frame_count=Count('items'))
                .order_by('-updated_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['drafts'] = (Essay.objects.filter(author__user=self.request.user, is_published=False)
                                 .annotate(frame_count=Count('items')))
        return context


class EssayDetailView(DetailView):
    template_name = 'essays/essay-detail.html'
    context_object_name = 'essay'

    def get_queryset(self):
        return Essay.visible_to(self.request.user).select_related('author__user', 'cover_photo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('photo')
        context['is_owner'] = self.object.is_owned_by(self.request.user)
        return context


class EssayCreateView(LoginRequiredMixin, CreateView):
    model = Essay
    form_class = EssayForm
    template_name = 'essays/essay-form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not Photographer.objects.filter(user=request.user).exists():
            messages.error(request, 'Нужен ви е профил на фотограф, за да създавате есета.')
            return redirect('user-profile-create')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'photographer': self.request.user.photographer}

    def form_valid(self, form):
        form.instance.author = self.request.user.photographer
        with transaction.atomic():
            response = super().form_valid(form)
            self.object.append_photos(form.cleaned_data['photos'])
        return response

    def get_success_url(self):
        # next step: put the frames in order and write the captions
        return reverse('essay-sequence', kwargs={'pk': self.object.pk})


class EssayUpdateView(EssayOwnerRequiredMixin, UpdateView):
    form_class = EssayForm
    template_name = 'essays/essay-form.html'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'photographer': self.object.author}

    def get_success_url(self):
        return reverse('essay-detail', kwargs={'pk': self.object.pk})


class EssayDeleteView(EssayOwnerRequiredMixin, DeleteView):
    template_name = 'essays/essay-delete.html'
    context_object_name = 'essay'
    success_url = reverse_lazy('essay-list')

    def form_valid(self, form):
        messages.success(self.request, f"Есето „{self.object.title}“ беше изтрито. Снимките остават.")
        return super().form_valid(form)


class EssaySequenceView(EssayOwnerRequiredMixin, SingleObjectMixin, View):
    """The sequence editor: order (drag and drop, or position numbers without
    JavaScript), editorial captions and removal, all saved in one POST, plus
    a form to add more of the author's photos."""
    template_name = 'essays/essay-sequence.html'
    context_object_name = 'essay'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render(AddPhotosForm(essay=self.object))

    def render(self, add_form):
        return render(self.request, self.template_name, {
            'essay': self.object,
            'items': self.object.items.select_related('photo'),
            'add_form': add_form,
        })

    def post(self, request, *args, **kwargs):
        self.object = essay = self.get_object()
        items = list(essay.items.all())

        def wanted_position(index_item):
            index, item = index_item
            try:
                return int(request.POST.get(f'position-{item.pk}', '')), index
            except ValueError:
                return index + 1, index  # unreadable number: keep its place

        ordered = [item for _, item in sorted(enumerate(items), key=wanted_position)]
        removed = [item for item in ordered if f'remove-{item.pk}' in request.POST]
        kept = [item for item in ordered if item not in removed]

        with transaction.atomic():
            for item in kept:
                caption = request.POST.get(f'caption-{item.pk}')
                if caption is not None and caption.strip() != item.caption:
                    item.caption = caption.strip()
                    item.save(update_fields=['caption'])
            if removed:
                if essay.cover_photo_id in {item.photo_id for item in removed}:
                    essay.cover_photo = None
                EssayItem.objects.filter(pk__in=[item.pk for item in removed]).delete()
            essay.reorder([item.pk for item in kept])
            essay.save()  # bumps updated_at, keeps the cover valid

        messages.success(request, 'Последователността е запазена.')
        return redirect('essay-sequence', pk=essay.pk)


class EssayAddPhotosView(EssayOwnerRequiredMixin, SingleObjectMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.object = essay = self.get_object()
        form = AddPhotosForm(request.POST, essay=essay)
        if form.is_valid():
            added = essay.append_photos(form.cleaned_data['photos'])
            essay.save()
            messages.success(request, f'Добавени кадри: {len(added)}.')
        else:
            messages.error(request, 'Изберете поне една от вашите снимки.')
        return redirect('essay-sequence', pk=essay.pk)
