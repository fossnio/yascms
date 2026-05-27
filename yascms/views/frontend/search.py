import datetime

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from yascms.enum import NavbarType, PageSize, LimitSize
from yascms.helpers import sanitize_input
from yascms.helpers.navbar import generate_navbar_trees
from yascms.dal import DAL


@view_config(route_name='search', renderer='')
def search_view(request):
    """前台顯示搜尋表單"""
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/search.jinja2'
    return {'navbar_trees': generate_navbar_trees(request, visible_only=True),
            'NavbarType': NavbarType}


@view_config(route_name='search_results', renderer='')
def search_results_view(request):
    """前台顯示搜尋結果"""
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/search_results.jinja2'
    quantity_per_page = sanitize_input(request.GET.get('q', 20), int, 20)
    if not (PageSize.MIN <= quantity_per_page < PageSize.MAX):
        raise HTTPNotFound()
    page_number = sanitize_input(request.GET.get('p', 1), int, 1)
    if not (LimitSize.MIN <= page_number < LimitSize.MAX):
        raise HTTPNotFound()
    try:
        key   = request.GET['key']
        value = request.GET['value']
        if key not in ('publisher', 'title', 'content'):
            raise HTTPNotFound()
        if value.strip() == '':
            raise HTTPNotFound()

        results = DAL.get_search_results(key, value, quantity_per_page, page_number)
        return {'navbar_trees': generate_navbar_trees(request, visible_only=True),
                'NavbarType': NavbarType,
                'page_quantity_of_total_results': DAL.get_page_quantity_of_total_search_results(quantity_per_page, key, value),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page,
                'results': results}
    except KeyError:
        raise HTTPNotFound()

