from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from tp_yass.forms.backend.telext import TelExtForm
from tp_yass.dal import DAL


@view_defaults(route_name='backend_telext_create', renderer='tp_yass:themes/default/backend/telext_create.jinja2', permission='edit')
class TelExtCreateView:
    """建立分機表的 view"""

    def __init__(self, request):
        self.request = request

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
            return HTTPFound(self.request.route_url('backend_telext_list'))
        return {'form': form}


@view_defaults(route_name='backend_telext_list', renderer='themes/default/backend/telext_list.jinja2', permission='view')
class TelExtListView:
    """顯示分機表的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config(request_method='GET')
    def get_view(self):
        """顯示分機表的列表"""
        telext_list = DAL.get_telext_list()
        return {'telext_list': telext_list}


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
        return HTTPFound(self.request.route_url('backend_telext_list'))


@view_defaults(route_name='backend_telext_edit',
               renderer='themes/default/backend/telext_edit.jinja2',
               permission='edit')
class TelExtEditView:

    def __init__(self, context, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

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
                return HTTPFound(self.request.route_url('backend_telext_list'))
            else:
                self.request.flash('telext 物件不存在', 'fail')
        return {'form': form}
