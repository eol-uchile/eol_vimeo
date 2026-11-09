# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging

# Installed packages (via pip)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Internal project dependencies
from eol_vimeo.thumbnail import get_thumbnail_url

logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def vimeo_thumbnail(request, vimeo_id):
    """
        Return the Vimeo thumbnail URL for vimeo_id as JSON.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'authentication required'}, status=401)
    return JsonResponse({'thumbnail_url': get_thumbnail_url(vimeo_id)})
