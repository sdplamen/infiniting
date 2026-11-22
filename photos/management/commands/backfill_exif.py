import io
import urllib.request

from django.core.management.base import BaseCommand

from photos.exif import extract_exif
from photos.models import Photo


class Command(BaseCommand):
    help = 'Fill Photo.exif for photos uploaded before EXIF was saved at upload time.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='re-read every photo, not only ones with empty exif')

    def handle(self, *args, **options):
        photos = Photo.objects.all() if options['all'] else Photo.objects.filter(exif={})
        filled = empty = failed = 0
        for photo in photos.iterator():
            if not photo.image:
                continue
            # the untransformed original, which still carries its EXIF
            url = photo.image.build_url(secure=True)
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    data = response.read()
            except Exception as error:
                failed += 1
                self.stderr.write(f'photo {photo.pk}: {error}')
                continue
            exif = extract_exif(io.BytesIO(data))
            # update() skips Photo.save(), so nothing is re-uploaded
            Photo.objects.filter(pk=photo.pk).update(exif=exif)
            if exif:
                filled += 1
            else:
                empty += 1
        self.stdout.write(self.style.SUCCESS(
            f'EXIF saved for {filled} photo(s); {empty} had none; {failed} failed to download.'
        ))
