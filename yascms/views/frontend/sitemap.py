from pyramid.view import view_config

from yascms.enum import NavbarType
from yascms.helpers.navbar import generate_navbar_trees

@view_config(route_name='sitemap', renderer='')
def sitemap_view(request):
    """顯示網站導覽"""
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/sitemap.jinja2'
    return {'navbar_trees': generate_navbar_trees(request, visible_only=True), 'NavbarType': NavbarType}
