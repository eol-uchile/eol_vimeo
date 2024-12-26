# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging

# Installed packages (via pip)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone

# Edx dependencies
from cms.djangoapps.contentstore.views import videos
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

# Internal project dependencies
from eol_vimeo.models import EolVimeoVideo
from eol_vimeo.vimeo_utils import update_image, validate_course, validate_user

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

def vimeo_update_picture(request):
    """
        Update video picture
    """
    if request.method != "POST":
        logger.error("EolVimeo - Wrong Method")
        return HttpResponse(status=400)
    edx_video_id = request.POST.get('videoid', '')
    course_id = request.POST.get('course_id', '')
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        logger.error("EolVimeo - Wrong course id: {}".format(course_id))
        return HttpResponse(status=400)
    if not validate_course(course_id):
       logger.error("EolVimeo - error validate course, invalid format: {}".format(course_id))
    if not validate_user(request.user, course_id):
       logger.error("EolVimeo - user dont have permission, user: {}, course: {}".format(request.user, course_id))
    if not EolVimeoVideo.objects.filter(edx_video_id=edx_video_id, course_key=course_key, status='upload_completed').exists():
        logger.error("EolVimeo - Video id have problem or status is not upload_completed, check model, edx_video_id: {}, course_id: {}".format(edx_video_id, course_id))
        return HttpResponse(status=400)
    response = update_image(edx_video_id, course_key)
    return JsonResponse(response)

def get_url_video(edx_video_id):
    bucket = videos.storage_service_bucket()
    key = videos.storage_service_key(bucket, file_name=edx_video_id)
    upload_url = key.generate_url(86400, 'GET')
    return upload_url
