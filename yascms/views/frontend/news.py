import datetime

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from yascms.enum import NavbarType, PageSize, LimitSize
from yascms.helpers import sanitize_input
from yascms.helpers.navbar import generate_navbar_trees
from yascms.dal import DAL


@view_config(route_name='news_list', renderer='')
def news_list_view(request):
    """前台顯示最新消息列表"""
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/news_list.jinja2'
    quantity_per_page = sanitize_input(request.GET.get('q', 20), int, 20)
    if not (PageSize.MIN <= quantity_per_page < PageSize.MAX):
        raise HTTPNotFound()
    category_id = sanitize_input(request.GET.get('c'), int, None)
    if (category_id is not None) and not (LimitSize.MIN <= category_id < LimitSize.MAX):
        raise HTTPNotFound()
    page_number = sanitize_input(request.GET.get('p', 1), int, 1)
    if not (LimitSize.MIN <= page_number < LimitSize.MAX):
        raise HTTPNotFound()

    news_list = DAL.get_frontend_news_list(page_number=page_number,
                                           quantity_per_page=quantity_per_page,
                                           category_id=category_id)
    return {'news_list': news_list,
            'news_category': DAL.get_news_category(category_id),
            'navbar_trees': generate_navbar_trees(request, visible_only=True),
            'today': datetime.date.today(),
            'page_quantity_of_total_news': DAL.get_page_quantity_of_total_news(quantity_per_page,
                                                                               category_id,
                                                                               visible_only=True),
            'page_number': page_number,
            'quantity_per_page': quantity_per_page,
            'NavbarType': NavbarType}


@view_config(route_name='news_get', renderer='')
def news_get_view(request):
    """前台顯示單一最新消息"""
    request.override_renderer = f'themes/{request.effective_theme_name}/frontend/news_get.jinja2'
    news_id = int(request.matchdict['news_id'])
    news = DAL.get_frontend_news(news_id)
    if news:
        return {'navbar_trees': generate_navbar_trees(request, visible_only=True),
                'NavbarType': NavbarType,
                'news': news}
    else:
        raise HTTPNotFound()
