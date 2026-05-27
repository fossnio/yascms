import logging

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from yascms.forms.backend.telext import TelExtForm
from yascms.dal import DAL


logger = logging.getLogger(__name__)


@view_defaults(route_name='backend_telext_create', renderer='', permission='edit')
class TelExtCreateView:
    """建立分機表的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/telext_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立分機表表單"""
        form = TelExtForm()
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """處理建立分機表表單"""
        form = TelExtForm(self.request.POST)
        if form.validate():
            DAL.create_telext(form)
            msg = f'分機 {form.title.data} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_telext_list'))
        return {'form': form}


@view_defaults(route_name='backend_telext_list', renderer='', permission='view')
class TelExtListView:
    """顯示分機表的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/telext_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示分機表的列表"""
        telext_list = DAL.get_telext_list()
        return {'telext_list': telext_list}


# TODO: 改用 post 處理刪除
@view_defaults(route_name='backend_telext_delete',
               permission='edit')
class TelExtDeleteView:
    """刪除分機表，只有管理者可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的分機"""
        telext_id = int(self.request.matchdict['telext_id'])
        DAL.delete_telext(telext_id)
        msg = f'分機 ID {telext_id} 刪除成功'
        logger.info(msg)
        self.request.session.flash(msg, 'success')
        return HTTPFound(self.request.route_url('backend_telext_list'))


@view_defaults(route_name='backend_telext_edit',
               renderer='',
               permission='edit')
class TelExtEditView:

    def __init__(self, context, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/telext_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = TelExtForm(obj=DAL.get_telext(int(self.request.matchdict['telext_id'])))
        form.is_pinned.default = True if form.is_pinned.data else False
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        form = TelExtForm(self.request.POST)
        if form.validate():
            telext_id = int(self.request.matchdict['telext_id'])
            result = DAL.update_telext(telext_id, form)
            if result:
                msg = f'分機 ID {telext_id} 更新成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_telext_list'))
            else:
                logger.error('分機 ID %d 不存在', telext_id)
                raise HTTPNotFound()
        return {'form': form}
