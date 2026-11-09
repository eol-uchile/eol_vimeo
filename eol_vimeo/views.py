# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging

# Installed packages (via pip)
import boto3
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# Edx dependencies
from cms.djangoapps.contentstore.views import videos
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

# Internal project dependencies
from eol_vimeo.models import EolVimeoVideo
from eol_vimeo.vimeo_utils import validate_course, validate_user
from eol_vimeo.thumbnail import update_image

logger = logging.getLogger(__name__)

def vimeo_callback(request):
    """
        Get url to download video 
    """
    if request.method != "GET":
        return HttpResponse(status=400)
    if 'videoid' not in request.GET:
        return HttpResponse(status=400)
    if 'token' not in request.GET:
        return HttpResponse(status=400)
    edx_video_id = request.GET.get('videoid', '')
    token = request.GET.get('token', '')
    if not EolVimeoVideo.objects.filter(edx_video_id=edx_video_id, status__in=['vimeo_encoding', 'vimeo_upload', 'upload_completed_encoding'], token=token).exists():
        logger.error("EolVimeo - Video id have problem, check model, edx_video_id: {}, token: {}".format(edx_video_id, token))
        return HttpResponse(status=400)
    video_vimeo = EolVimeoVideo.objects.get(edx_video_id=edx_video_id, token=token)
    now = timezone.now()
    if now >= video_vimeo.expiry_at:
        logger.error("EolVimeo - expiration date is greater than or equal datetime now, edx_video_id: {}, now: {}, expiry_at: {}".format(edx_video_id, now, video_vimeo.expiry_at))
        return HttpResponse(status=400)
    upload_url = get_url_video(edx_video_id)
    return HttpResponseRedirect(upload_url)

@require_http_methods(['GET'])
def vimeo_update_thumbnail(request, vimeo_id):
    """
        Update video thumbnail
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'authentication required'}, status=401)
    videos = EolVimeoVideo.objects.filter(vimeo_video_id=vimeo_id, status='upload_completed')
    if not videos.exists():
        logger.error("EolVimeo - Video associated to that Vimeo id have problem or status is not upload_completed, check model, vimeo_id: {}".format(vimeo_id))
        return HttpResponse(status=400)
    course_ids = set(str(course_key) for course_key in videos.values_list('course_key', flat=True))
    if not any(validate_user(request.user, course_id) for course_id in course_ids):
        logger.error("EolVimeo - user dont have permission, user: {}, vimeo_id: {}".format(request.user, vimeo_id))
        return HttpResponse(status=403)
    response = update_image(vimeo_id)
    return JsonResponse(response)

def get_url_video(edx_video_id):
    video_session = boto3.Session(profile_name='video_uploads')
    s3_client = video_session.client('s3', endpoint_url=settings.AWS_S3_ENDPOINT_URL)
    upload_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': videos.storage_service_bucket_name(),
                'Key': videos.storage_service_key_name(edx_video_id),
            },
            ExpiresIn=videos.KEY_EXPIRATION_IN_SECONDS,
        )
    return upload_url
