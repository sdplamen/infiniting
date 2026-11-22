"""Read a small, display-ready subset of EXIF from an uploaded image.

Only camera/exposure fields are kept. GPS and other identifying data are
deliberately dropped, because the result is shown publicly on the photo page.
"""
from datetime import datetime
from fractions import Fraction

from PIL import Image

EXIF_IFD = 0x8769

# stored key -> label shown on the photo page (order is display order)
EXIF_LABELS = {
    'camera': 'Камера',
    'lens': 'Обектив',
    'exposure': 'Експонация',
    'aperture': 'Бленда',
    'iso': 'ISO',
    'focal_length': 'Фокусно разстояние',
    'taken_at': 'Заснета на',
}

# EXIF tag ids
MAKE, MODEL, DATETIME = 0x010F, 0x0110, 0x0132
EXPOSURE_TIME, F_NUMBER, ISO = 0x829A, 0x829D, 0x8827
DATETIME_ORIGINAL, FOCAL_LENGTH, FOCAL_35MM, LENS_MODEL = 0x9003, 0x920A, 0xA405, 0xA434


def _text(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'ignore')
    return str(value).replace('\x00', '').strip() if value is not None else ''


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _fmt(num):
    return f'{num:.2f}'.rstrip('0').rstrip('.')


def _exposure(value):
    seconds = _number(value)
    if not seconds or seconds <= 0:
        return ''
    if seconds >= 1:
        return f'{_fmt(seconds)} s'
    return f'1/{round(1 / seconds)} s' if (1 / seconds) >= 1.5 else f'{Fraction(seconds).limit_denominator(10)} s'


def _taken_at(value):
    try:
        return datetime.strptime(_text(value)[:19], '%Y:%m:%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
    except ValueError:
        return ''


def extract_exif(fileobj):
    """Return {key: formatted string} for the keys in EXIF_LABELS; {} if none/unreadable."""
    try:
        if hasattr(fileobj, 'seek'):
            fileobj.seek(0)
        with Image.open(fileobj) as image:
            base = image.getexif()
            sub = base.get_ifd(EXIF_IFD)
    except Exception:  # not an image, truncated file, broken EXIF block...
        return {}
    finally:
        if hasattr(fileobj, 'seek'):
            fileobj.seek(0)

    def tag(tag_id):
        return sub.get(tag_id, base.get(tag_id))

    make, model = _text(tag(MAKE)), _text(tag(MODEL))
    camera = model if model.lower().startswith(make.lower()) else f'{make} {model}'.strip()

    iso = tag(ISO)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None

    focal = _number(tag(FOCAL_LENGTH))
    focal_35 = _number(tag(FOCAL_35MM))
    focal_text = f'{_fmt(focal)} mm' if focal else ''
    if focal_text and focal_35 and round(focal_35) != round(focal):
        focal_text += f' ({round(focal_35)} mm екв.)'

    aperture = _number(tag(F_NUMBER))

    data = {
        'camera': camera,
        'lens': _text(tag(LENS_MODEL)),
        'exposure': _exposure(tag(EXPOSURE_TIME)),
        'aperture': f'f/{_fmt(aperture)}' if aperture else '',
        'iso': _text(iso) if iso else '',
        'focal_length': focal_text,
        'taken_at': _taken_at(tag(DATETIME_ORIGINAL) or tag(DATETIME)),
    }
    return {key: value for key, value in data.items() if value}
