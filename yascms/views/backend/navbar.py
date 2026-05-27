import logging

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden

from yascms.enum import NavbarType
from yascms.helpers.navbar import generate_navbar_trees
from yascms.forms.backend.navbar import NavbarForm, NavbarEditForm
from yascms.dal import DAL


logger = logging.getLogger(__name__)


@view_defaults(route_name='backend_navbar_list',
               renderer='',
               permission='view')
class NavbarListView:

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/navbar_list.jinja2'

    @view_config()
    def list_view(self):
        """後台顯示 navbar 樹狀結構"""
        return {'navbar_trees': generate_navbar_trees(self.request)}


@view_defaults(route_name='backend_navbar_create',
               renderer='',
               permission='edit')
class NavbarCreateView:
    """建立巢狀選單"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/navbar_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = NavbarForm()
        return {'form': form,
                'navbar_trees': generate_navbar_trees(self.request, type='intermediate'),
                'NavbarType': NavbarType}

    @view_config(request_method='POST')
    def post_view(self):
        form = NavbarForm(self.request.POST)
        if form.validate():
            if DAL.create_navbar(form):
                msg = f'導覽列 {form.name.data} 建立成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_navbar_list'))
            else:
                msg = f'導覽列 {form.name.data} 建立失敗，請查閱 log'
                logger.error(msg)
                self.request.session.flash(msg, 'fail')
        return {'form': form,
                'navbar_trees': generate_navbar_trees(self.request, type='intermediate'),
                'NavbarType': NavbarType}


@view_defaults(route_name='backend_navbar_delete', permission='edit')
class NavbarDeleteView:
    """刪除 navbar 與其下面的所有選單"""

    def __init__(self, request):
        self.request = request

    @view_config()
    def delete_view(self):
        """將整串導覽列刪除"""
        # TODO: 要做成讓使用者決定要整串刪掉還是孤兒的節點都搬移至未指定
        navbar_id = int(self.request.matchdict['navbar_id'])
        if navbar_id == 1:
            logger.error('內建的根導覽列不可刪除')
            return HTTPForbidden()
        navbar = DAL.get_navbar(navbar_id)
        if navbar:
            DAL.change_navbar_ancestor_id(navbar_id, navbar.ancestor_id)
            DAL.delete_navbar(navbar)
            msg = f'導覽列 {navbar.name} 刪除成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
        else:
            logger.error('找不到導覽列 ID %d', navbar_id)
            return HTTPForbidden()
        return HTTPFound(self.request.route_url('backend_navbar_list'))


@view_defaults(route_name='backend_navbar_edit',
               renderer='',
               permission='edit')
class NavbarEditView:

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/navbar_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        navbar_id = int(self.request.matchdict['navbar_id'])
        navbar = DAL.get_navbar(navbar_id)

        form = NavbarEditForm(name=navbar.name,
                              type=navbar.type,
                              aria_name=navbar.aria_name,
                              url=navbar.url,
                              icon=navbar.icon,
                              order=navbar.order)
        if navbar.page:
            form.leaf_type.data = 1
            form.page_id.data = navbar.page.id
        else:
            form.leaf_type.data = 2
        form.is_href_blank.data = True if navbar.is_href_blank else False
        form.is_visible.data = True if navbar.is_visible else False
        if navbar.ancestor:
            form.ancestor_id.data = navbar.ancestor.id
        return {'form': form,
                'navbar_trees': generate_navbar_trees(self.request, type='intermediate', excluded_id=navbar_id),
                'NavbarType': NavbarType}

    @view_config(request_method='POST')
    def post_view(self):
        navbar_id = int(self.request.matchdict['navbar_id'])
        navbar = DAL.get_navbar(navbar_id)
        if navbar:
            form = NavbarEditForm(self.request.POST)
            if form.validate():
                if DAL.sync_navbar(form, navbar):
                    msg = f'導覽列 {navbar.name} 修改成功'
                    logger.info(msg)
                    self.request.session.flash(msg, 'success')
                    return HTTPFound(self.request.route_url('backend_navbar_list'))
                else:
                    msg = f'導覽列 ID {navbar_id} 修改失敗'
                    logger.error(msg)
                    self.request.session.flash(msg, 'fail')
        else:
            logger.error('找不到導覽列 ID %d', navbar_id)
            raise HTTPNotFound()
        return {'form': form,
                'navbar_trees': generate_navbar_trees(self.request, type='intermediate', excluded_id=navbar_id),
                'NavbarType': NavbarType}
