from django.conf.urls import url

from .views_lms import vimeo_thumbnail

urlpatterns = (
    url(
        r'^eolvimeo/thumbnail/(?P<vimeo_id>\d+)$',
        vimeo_thumbnail,
        name='vimeo_thumbnail',
    ),
)
