from pyramid.view import (notfound_view_config,
                          forbidden_view_config)


@notfound_view_config(renderer='', append_slash=True)
def notfound_view(request):
    request.override_renderer = f'themes/{request.effective_theme_name}/404.jinja2'
    request.response.status_code = 404
    return {}


@forbidden_view_config(renderer='')
def forbidden_view(request):
    request.override_renderer = f'themes/{request.effective_theme_name}/403.jinja2'
    request.response.status_code = 403
    return {}
