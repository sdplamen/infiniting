"""Direct uploads: the browser sends the photo straight to Cloudinary.

Without this, a photo travels browser → Django → Cloudinary while the user
waits. With it, Django only signs the upload (so nobody can upload into the
account without asking us), the browser uploads while the caption is being
written, and the form then submits the uploaded file's reference, which we
accept only if Cloudinary's response signature proves it is genuine.

static/js/direct-upload.js is the browser side. Without JavaScript, or if the
direct upload fails, the form falls back to the normal file upload.
"""
import re
import time

import cloudinary
from cloudinary import CloudinaryResource
from cloudinary.utils import api_sign_request, verify_api_response_signature

UPLOAD_FOLDER = 'photos'                      # same folder as Photo.image (CloudinaryField(folder='photos'))
ALLOWED_FORMATS = 'jpg,jpeg,png,webp,heic,heif,tif,tiff'
_PUBLIC_ID = re.compile(rf'^{UPLOAD_FOLDER}/[\w\-./]{{1,200}}$')
_FORMAT = re.compile(r'^[a-z0-9]{2,5}$')


def upload_signature():
    """Signed parameters for one browser upload (valid for an hour, Cloudinary's limit)."""
    config = cloudinary.config()
    params = {
        'timestamp': int(time.time()),
        'folder': UPLOAD_FOLDER,
        'allowed_formats': ALLOWED_FORMATS,
    }
    return {
        **params,
        'signature': api_sign_request(params, config.api_secret),
        'api_key': config.api_key,
        'upload_url': f'https://api.cloudinary.com/v1_1/{config.cloud_name}/image/upload',
    }


def verified_resource(public_id, version, signature, image_format):
    """The uploaded image as a CloudinaryResource, or None unless Cloudinary signed this exact
    public_id and version (so a form can't point a photo at an arbitrary or forged file)."""
    public_id, version = str(public_id or ''), str(version or '')
    if not (_PUBLIC_ID.match(public_id) and version.isdigit() and _FORMAT.match(image_format or '')):
        return None
    if not verify_api_response_signature(public_id, version, signature or ''):
        return None
    return CloudinaryResource(public_id, format=image_format, version=version, type='upload', resource_type='image')
