# Installed packages (via pip)
from django.conf.urls import url

# Internal project dependencies
from .views import vimeo_callback, vimeo_update_picture

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
)
