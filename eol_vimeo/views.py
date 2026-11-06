# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging

# Installed packages (via pip)
import boto3
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

# Edx dependencies
from cms.djangoapps.contentstore.views import videos

# Internal project dependencies
from eol_vimeo.models import EolVimeoVideo

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
