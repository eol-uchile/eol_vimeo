import os
import eol_vimeo

def plugin_settings(settings):
    settings.EOL_VIMEO_CLIENT_ID = ''
    settings.EOL_VIMEO_CLIENT_SECRET = ''
    settings.EOL_VIMEO_CLIENT_TOKEN = ''
    settings.EOL_VIMEO_MAIN_FOLDER = None
    settings.EOL_VIMEO_DOMAINS = []

    template_path = os.path.join(os.path.dirname(eol_vimeo.__file__), "templates")
    # Add app template path to the base list, so its included on mako lookups
    if hasattr(settings, 'MAKO_TEMPLATE_DIRS_BASE'):
        settings.MAKO_TEMPLATE_DIRS_BASE.append(template_path)
