from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from essays.models import Essay, EssayItem
from photos.models import Photo

UserModel = get_user_model()


class EssayTestCase(TestCase):
    """An author with four photos, an essay of three of them, and another user."""

    def setUp(self):
        self.author = UserModel.objects.create_user(username='author', password='pw-12345678')
        self.other = UserModel.objects.create_user(username='other', password='pw-12345678')
        self.photographer = self.author.photographer          # created by the users signal
        self.photos = [Photo.objects.create(author=self.photographer, image=f'photos/p{i}', caption=f'p{i}')
                       for i in range(4)]
        self.foreign_photo = Photo.objects.create(author=self.other.photographer, image='photos/x', caption='x')
        self.essay = Essay.objects.create(author=self.photographer, title='Улицата', is_published=True)
        self.essay.append_photos(self.photos[:3])

    def items(self, essay=None):
        return list((essay or self.essay).items.values_list('photo__caption', 'position', 'caption'))

    def url(self, name, essay=None):
        return reverse(name, kwargs={'pk': (essay or self.essay).pk})


class EssayModelTest(EssayTestCase):
    def test_append_keeps_order_and_skips_duplicates(self):
        added = self.essay.append_photos([self.photos[3], self.photos[0]])
        self.assertEqual(len(added), 1)
        self.assertEqual([(c, p) for c, p, _ in self.items()], [('p0', 1), ('p1', 2), ('p2', 3), ('p3', 4)])

    def test_reorder_requires_every_item_once(self):
        ids = list(self.essay.items.values_list('pk', flat=True))
        self.essay.reorder([ids[2], ids[0], ids[1]])
        self.assertEqual([c for c, _, _ in self.items()], ['p2', 'p0', 'p1'])
        for bad in ([ids[0], ids[1]], [ids[0], ids[0], ids[1]], ids + [999]):
            with self.assertRaises(ValueError):
                self.essay.reorder(bad)

    def test_cover_falls_back_to_first_frame(self):
        self.assertEqual(self.essay.cover, self.photos[0])
        self.essay.cover_photo = self.photos[2]
        self.assertEqual(self.essay.cover, self.photos[2])
        self.assertEqual(self.essay.triptych(), [self.photos[2], self.photos[0], self.photos[1]])

    def test_deleting_a_photo_removes_its_frame(self):
        self.essay.cover_photo = self.photos[1]
        self.essay.save()
        self.photos[1].delete()
        self.essay.refresh_from_db()
        self.assertIsNone(self.essay.cover_photo)
        self.assertEqual([c for c, _, _ in self.items()], ['p0', 'p2'])


class EssayVisibilityTest(EssayTestCase):
    def test_published_essay_is_public_with_frames_in_order(self):
        EssayItem.objects.filter(essay=self.essay, photo=self.photos[1]).update(caption='Здрач на моста')
        page = self.client.get(self.url('essay-detail'))
        self.assertContains(page, 'Улицата')
        self.assertContains(page, 'Здрач на моста')
        self.assertContains(page, 'id="frame-3"')
        self.assertNotContains(page, self.url('essay-sequence'))   # no owner tools
        self.assertContains(self.client.get(reverse('essay-list')), 'Улицата')

    def test_draft_only_for_its_author(self):
        draft = Essay.objects.create(author=self.photographer, title='Чернова-есе')
        self.assertEqual(self.client.get(self.url('essay-detail', draft)).status_code, 404)
        self.assertNotContains(self.client.get(reverse('essay-list')), 'Чернова-есе')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('essay-detail', draft)).status_code, 404)
        self.client.force_login(self.author)
        self.assertContains(self.client.get(self.url('essay-detail', draft)), 'Чернова-есе')
        self.assertContains(self.client.get(reverse('essay-list')), 'Вашите чернови')

    def test_contact_sheet_numbers_frames(self):
        self.essay.kind = Essay.Kind.CONTACT_SHEET
        self.essay.save()
        page = self.client.get(self.url('essay-detail'))
        self.assertContains(page, 'class="contact-sheet__frame"', count=3)
        self.assertContains(page, '3 EXP')

    def test_every_cover_layout_renders(self):
        for layout in Essay.CoverLayout.values:
            self.essay.cover_layout = layout
            self.essay.save()
            page = self.client.get(self.url('essay-detail'))
            self.assertContains(page, f'essay-cover--{layout}')
        empty = Essay.objects.create(author=self.photographer, title='Празно', is_published=True)
        self.assertContains(self.client.get(self.url('essay-detail', empty)), 'essay-cover--no-photo')

    def test_profile_lists_essays(self):
        Essay.objects.create(author=self.photographer, title='Чернова-есе')
        profile = reverse('user-profile-detail', kwargs={'pk': self.photographer.pk})
        page = self.client.get(profile)
        self.assertContains(page, 'Улицата')
        self.assertNotContains(page, 'Чернова-есе')
        self.client.force_login(self.author)
        self.assertContains(self.client.get(profile), 'Чернова-есе')


class EssayCreateEditTest(EssayTestCase):
    def test_create_with_photos_goes_to_sequence_editor(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('essay-create'), {
            'title': 'Пристанище', 'intro': 'Увод', 'kind': 'essay', 'cover_layout': 'split',
            'photos': [self.photos[3].pk, self.photos[1].pk],
        })
        essay = Essay.objects.get(title='Пристанище')
        self.assertRedirects(response, self.url('essay-sequence', essay))
        self.assertEqual(essay.author, self.photographer)
        self.assertFalse(essay.is_published)
        self.assertEqual([c for c, _, _ in self.items(essay)], ['p1', 'p3'])  # upload order

    def test_cannot_use_someone_elses_photo(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('essay-create'), {
            'title': 'Чуждо', 'kind': 'essay', 'cover_layout': 'full_bleed', 'photos': [self.foreign_photo.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Essay.objects.filter(title='Чуждо').exists())

        response = self.client.post(self.url('essay-add-photos'), {'photos': [self.foreign_photo.pk]})
        self.assertFalse(self.essay.items.filter(photo=self.foreign_photo).exists())

    def test_cover_photo_must_be_in_the_essay(self):
        self.client.force_login(self.author)
        data = {'title': 'Улицата', 'kind': 'essay', 'cover_layout': 'full_bleed', 'is_published': 'on'}
        response = self.client.post(self.url('essay-edit'), {**data, 'cover_photo': self.photos[3].pk})
        self.assertEqual(response.status_code, 200)   # p3 isn't a frame of this essay
        response = self.client.post(self.url('essay-edit'), {**data, 'cover_photo': self.photos[2].pk,
                                                            'cover_layout': 'triptych'})
        self.assertRedirects(response, self.url('essay-detail'))
        self.essay.refresh_from_db()
        self.assertEqual((self.essay.cover_photo, self.essay.cover_layout), (self.photos[2], 'triptych'))

    def test_only_author_edits_or_deletes(self):
        self.client.force_login(self.other)
        for name in ('essay-edit', 'essay-sequence', 'essay-delete'):
            self.assertEqual(self.client.get(self.url(name)).status_code, 403)
        self.assertEqual(self.client.post(self.url('essay-delete')).status_code, 403)
        self.assertEqual(self.client.post(self.url('essay-add-photos'), {'photos': [self.photos[3].pk]}).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get(reverse('essay-create')), f"{reverse('login')}?next={reverse('essay-create')}")

    def test_delete_keeps_photos(self):
        self.client.force_login(self.author)
        self.assertRedirects(self.client.post(self.url('essay-delete')), reverse('essay-list'))
        self.assertFalse(Essay.objects.exists())
        self.assertFalse(EssayItem.objects.exists())
        self.assertEqual(Photo.objects.count(), 5)


class EssaySequenceEditorTest(EssayTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.author)
        self.ids = list(self.essay.items.values_list('pk', flat=True))

    def post(self, **fields):
        return self.client.post(self.url('essay-sequence'), fields)

    def test_editor_page(self):
        page = self.client.get(self.url('essay-sequence'))
        self.assertContains(page, 'class="sequence-item"', count=3)
        self.assertContains(page, f'name="position-{self.ids[0]}" value="1"')
        self.assertContains(page, 'js/essay-sequence.js')
        self.assertContains(page, 'p3')                     # p3 can still be added

    def test_reorder_caption_and_remove_in_one_save(self):
        self.essay.cover_photo = self.photos[1]
        self.essay.save()
        response = self.post(**{
            f'position-{self.ids[0]}': '3', f'position-{self.ids[1]}': '2', f'position-{self.ids[2]}': '1',
            f'caption-{self.ids[2]}': '  Начало  ', f'caption-{self.ids[0]}': 'Край',
            f'remove-{self.ids[1]}': 'on',
        })
        self.assertRedirects(response, self.url('essay-sequence'))
        self.assertEqual(self.items(), [('p2', 1, 'Начало'), ('p0', 2, 'Край')])
        self.essay.refresh_from_db()
        self.assertIsNone(self.essay.cover_photo)            # its cover frame was removed

    def test_ties_and_bad_numbers_keep_current_order(self):
        # p0 → 3; p1 unreadable, so it keeps its place (2); p2 → 2 ties with p1 and stays after it
        self.post(**{f'position-{self.ids[0]}': '3', f'position-{self.ids[1]}': 'x', f'position-{self.ids[2]}': '2'})
        self.assertEqual([(c, p) for c, p, _ in self.items()], [('p1', 1), ('p2', 2), ('p0', 3)])

    def test_add_photos_appends(self):
        self.client.post(self.url('essay-add-photos'), {'photos': [self.photos[3].pk]})
        self.assertEqual([(c, p) for c, p, _ in self.items()], [('p0', 1), ('p1', 2), ('p2', 3), ('p3', 4)])


class EssayLightboxTest(EssayTestCase):
    def lightbox(self, photo, **params):
        return self.client.get(reverse('photo-full-photo', kwargs={'pk': photo.pk}), params)

    def lb_url(self, photo):
        return f"{reverse('photo-full-photo', kwargs={'pk': photo.pk})}?essay={self.essay.pk}"

    def test_arrows_follow_the_essay(self):
        ids = list(self.essay.items.values_list('pk', flat=True))
        self.essay.reorder([ids[2], ids[0], ids[1]])           # p2, p0, p1
        page = self.lightbox(self.photos[0], essay=self.essay.pk)
        self.assertEqual(page.context['prev_url'], self.lb_url(self.photos[2]))
        self.assertEqual(page.context['next_url'], self.lb_url(self.photos[1]))
        self.assertEqual((page.context['position'], page.context['total']), (2, 3))
        self.assertEqual(page.context['close_url'], f"{self.url('essay-detail')}#frame-2")
        self.assertContains(page, 'class="lb-essay">Улицата<')

    def test_essay_page_links_into_the_lightbox(self):
        self.assertContains(self.client.get(self.url('essay-detail')), f'href="{self.lb_url(self.photos[1])}"')

    def test_falls_back_to_feed_for_unknown_hidden_or_unrelated_essay(self):
        draft = Essay.objects.create(author=self.photographer, title='Скрито')
        draft.append_photos(self.photos)
        for params in ({'essay': draft.pk}, {'essay': 'abc'}, {'essay': 9999}):
            page = self.lightbox(self.photos[0], **params)
            self.assertNotIn('essay', page.context)
        page = self.lightbox(self.photos[3], essay=self.essay.pk)   # p3 isn't in this essay
        self.assertNotIn('essay', page.context)
