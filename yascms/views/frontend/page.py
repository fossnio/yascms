from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from yascms.enum import NavbarType
from yascms.helpers.navbar import generate_navbar_trees
from yascms.dal import DAL


@view_config(route_name='page_get', renderer='')
def page_get_view(request):
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/page_get.jinja2'
    page = DAL.get_page(request.matchdict['page_id'])
    if page:
        return {'navbar_trees': generate_navbar_trees(request, visible_only=True),
                'page': page,
                'NavbarType': NavbarType}
    else:
        raise HTTPNotFound()
