# -*- coding: utf-8 -*-
# Python Standard Libraries
import logging

# Installed packages (via pip)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Internal project dependencies
from eol_vimeo.thumbnail import get_thumbnail_url

logger = logging.getLogger(__name__)

@require_http_methods(['GET', 'POST'])
def vimeo_thumbnail(request, vimeo_id):
    """
        Return the Vimeo thumbnail URL for vimeo_id as JSON. POST forces the refresh from Vimeo.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'authentication required'}, status=401)
    force = request.method == 'POST'
    return JsonResponse({'thumbnail_url': get_thumbnail_url(vimeo_id, force=force)})
