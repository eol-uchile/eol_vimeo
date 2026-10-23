from django.conf.urls import url

# Internal project dependencies
from .views import vimeo_callback, vimeo_update_picture
from .views_lms import vimeo_thumbnail

urlpatterns = (
    url(
        r'^eolvimeo/callback',
        vimeo_callback,
        name='vimeo_callback',
    ),
    url(
        r'^eolvimeo/update_picture',
        vimeo_update_picture,
        name='vimeo_update_picture',
    ),
    # For preview in Studio
    url(
        r'^eolvimeo/thumbnail/(?P<vimeo_id>\d+)$',
        vimeo_thumbnail,
        name='vimeo_thumbnail',
    ),
)
