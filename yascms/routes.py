from .resources import (auth_user_factory,
                        admin_factory,
                        page_edit_factory,
                        staff_factory,
                        news_edit_factory,
                        link_edit_factory)


def includeme(config):

    # frontend
    def preview_override_param(request, elements, kwargs):
        """override_theme_name 這個 query param 可以用來暫時覆蓋 request.current_theme ，用在預覽樣板用。
        所以一旦 url 上出現了 override_theme_name 且其值不為空，就要全部自動的加在所有 route_url 後"""
        query = kwargs.setdefault('_query', {})
        if request.GET.get('override_theme_name', None):
            query.setdefault('override_theme_name', request.GET['override_theme_name'])
        return elements, kwargs

    config.add_route('homepage', '/', pregenerator=preview_override_param)
    config.add_route('news_list', '/news/list', pregenerator=preview_override_param)
    config.add_route('news_get', r'/news/get/{news_id:\d+}', pregenerator=preview_override_param)
    config.add_route('telext', '/telext', pregenerator=preview_override_param)
    config.add_route('links', '/links', pregenerator=preview_override_param)
    config.add_route('page_get', r'/page/get/{page_id:\d+}', pregenerator=preview_override_param)
    config.add_route('login', '/login', pregenerator=preview_override_param)
    config.add_route('logout', '/logout', pregenerator=preview_override_param)
    config.add_route('search', '/search', pregenerator=preview_override_param)
    config.add_route('search_results', '/search_results', pregenerator=preview_override_param)
    config.add_route('sitemap', '/sitemap', pregenerator=preview_override_param)

    config.add_route('oauth2_provider_login', '/oauth2/{provider_name}/login')
    config.add_route('oauth2_provider_callback', '/oauth2/{provider_name}/callback')

    # backend
    config.add_route('backend_homepage', '/backend/', factory=auth_user_factory, pregenerator=preview_override_param)

    config.add_route('backend_site_config_edit', '/backend/site/config/edit', factory=admin_factory,
                                                                              pregenerator=preview_override_param)

    config.add_route('backend_theme_config_list', '/backend/theme_config/list', factory=admin_factory,
                                                                                pregenerator=preview_override_param)
    config.add_route('backend_theme_config_activate', '/backend/theme_config/activate/{theme_name}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_theme_config_delete', '/backend/theme_config/delete/{theme_name}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_theme_config_general_edit', '/backend/theme_config/general/edit/{theme_name}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_banners_edit', '/backend/theme_config/banners/edit/{theme_name}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_banners_delete',
                     '/backend/theme_config/banners/delete/{theme_name}/{banner_name}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_banners_upload', '/backend/theme_config/banners/upload/{theme_name}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_upload', '/backend/theme_config/upload',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_homepage_items_order_edit', '/backend/theme_config/{theme_name}/homepage_items_order/edit',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_theme_config_download', '/backend/theme_config/{theme_name}/download',
                     factory=admin_factory, pregenerator=preview_override_param)

    config.add_route('backend_navbar_create', '/backend/navbar/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_navbar_list', '/backend/navbar/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_navbar_delete', r'/backend/navbar/delete/{navbar_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_navbar_edit', r'/backend/navbar/edit/{navbar_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_user_create', '/backend/user/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_user_list', '/backend/user/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_user_delete', r'/backend/user/delete/{user_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_user_edit', r'/backend/user/edit/{user_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_user_self_edit', '/backend/user/self/edit', factory=auth_user_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_group_create', '/backend/group/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_group_list', '/backend/group/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_group_delete', r'/backend/group/delete/{group_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_group_edit', r'/backend/group/edit/{group_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_page_create', '/backend/page/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_page_list', '/backend/page/list', factory=auth_user_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_page_delete', r'/backend/page/delete/{page_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_page_edit', r'/backend/page/edit/{page_id:\d+}', factory=page_edit_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_news_create', '/backend/news/create', factory=staff_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_news_list', '/backend/news/list', factory=auth_user_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_news_delete', r'/backend/news/delete/{news_id:\d+}', factory=news_edit_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_news_edit', r'/backend/news/edit/{news_id:\d+}', factory=news_edit_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_news_category_create', '/backend/news/category/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_news_category_list', '/backend/news/category/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_news_category_delete', r'/backend/news/category/delete/{news_category_id:\d+}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_news_category_edit', r'/backend/news/category/edit/{news_category_id:\d+}',
                     factory=admin_factory, pregenerator=preview_override_param)

    config.add_route('backend_link_create', '/backend/link/create', factory=staff_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_link_list', '/backend/link/list', factory=staff_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_link_delete', r'/backend/link/delete/{link_id:\d+}',
                     factory=link_edit_factory, pregenerator=preview_override_param)
    config.add_route('backend_link_edit', r'/backend/link/edit/{link_id:\d+}',
                     factory=link_edit_factory, pregenerator=preview_override_param)

    config.add_route('backend_link_category_create', '/backend/link/category/create',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_link_category_list', '/backend/link/category/list',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_link_category_delete', r'/backend/link/category/delete/{link_category_id:\d+}',
                     factory=admin_factory, pregenerator=preview_override_param)
    config.add_route('backend_link_category_edit', r'/backend/link/category/edit/{link_category_id:\d+}',
                     factory=admin_factory, pregenerator=preview_override_param)

    config.add_route('backend_telext_create', '/backend/telext/create', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_telext_list', '/backend/telext/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_telext_delete', r'/backend/telext/delete/{telext_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_telext_edit', r'/backend/telext/edit/{telext_id:\d+}', factory=admin_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_auth_log_list', '/backend/auth_log/list', factory=auth_user_factory,
                     pregenerator=preview_override_param)

    config.add_route('backend_api_token_list', '/backend/api_token/list', factory=admin_factory,
                     pregenerator=preview_override_param)
    config.add_route('backend_api_token_create', '/backend/api_token/create', factory=admin_factory,
                     pregenerator=preview_override_param)

    # 給後台 ajax 撈資料用的
    config.add_route('backend_json_page_list', '/backend/json/page/list', factory=admin_factory)
    config.add_route('backend_json_page_get', r'/backend/json/page/get/{page_id:\d+}', factory=admin_factory)
    config.add_route('backend_json_news_category_list', '/backend/json/news/category/list', factory=admin_factory)
    config.add_route('backend_json_link_category_list', '/backend/json/link/category/list', factory=admin_factory)

    config.add_route('backend_oauth2_integration_list', '/backend/oauth2/integration/list', factory=admin_factory)
    config.add_route('backend_oauth2_integration_edit', '/backend/oauth2/integration/{provider_name}/edit',
                     factory=admin_factory)

    # 開發用，上線環境會讓前端的 web server 處理這部份
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('uploads', 'uploads', cache_max_age=3600)
    config.add_static_view('', 'webroot', cache_max_age=3600)
