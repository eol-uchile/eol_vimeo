# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging
import re

# Internal project dependencies
from .models import EolVimeoVideo
from .vimeo_utils import get_client_vimeo

logger = logging.getLogger(__name__)

def fetch_vimeo_picture(vimeo_id):
    """
        Retrieves the thumbnail from the Vimeo API and stores it in EolVimeoVideo.url_picture for all rows with that vimeo_video_id.
    """
    client = get_client_vimeo()
    if client is None:
        return ''
    try:
        response = client.get('/videos/{}'.format(vimeo_id), params={'fields': 'pictures.type,pictures.base_link'})
    except Exception as e:
        logger.exception('EolVimeo - Thumbnail, exception vimeo_id: {}, error: {}'.format(vimeo_id, str(e)))
        return ''
    if response.status_code != 200:
        logger.info('EolVimeo - Thumbnail, vimeo_id: {}, status: {}, response: {}'.format(
            vimeo_id, response.status_code, response.text[:300]))
        return ''
    pictures = response.json().get('pictures') or {}
    url = pictures.get('base_link') or ''
    logger.info(pictures)
    if url and pictures.get('type') != 'default':
        EolVimeoVideo.objects.filter(vimeo_video_id=vimeo_id).update(url_picture=url)
    return url


def get_thumbnail_url(vimeo_id, force=False):
    """
        Returns thumbnail of a Vimeo video: EolVimeoVideo -> Vimeo API.
        With force=True skips the database and refreshes it from the Vimeo API.
    """
    if not vimeo_id:
        return ''
    if not force:
        stored = EolVimeoVideo.objects.filter(vimeo_video_id=vimeo_id).exclude(url_picture='').values_list('url_picture', flat=True).first()
        if stored is not None:
            return stored
    return fetch_vimeo_picture(vimeo_id)
