from django.conf.urls import url

# Internal project dependencies
from .views import vimeo_callback
from .views_lms import vimeo_thumbnail

urlpatterns = (
    url(
        r'^eolvimeo/callback',
        vimeo_callback,
        name='vimeo_callback',
    ),
    # For preview in Studio
    url(
        r'^eolvimeo/thumbnail/(?P<vimeo_id>\d+)$',
        vimeo_thumbnail,
        name='vimeo_thumbnail',
    ),
)
