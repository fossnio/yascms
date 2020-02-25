from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound

from tp_yass.forms.backend.page import PageForm, PageEditForm
from tp_yass.helper import sanitize_input
from tp_yass.views.backend.helper import upload_attachment, delete_attachment
from tp_yass.dal import DAL


@view_defaults(route_name='backend_page_create',
               renderer='themes/default/backend/page_create.jinja2',
               permission='edit')
class PageCreateView:
    """建立單一頁面的 view class"""

    def __init__(self, context, request):
        """
        Args:
            context: 因為頁面還未建立，所以 context 為管理者才有權限的 acl
            request: pyramid.request.Request
        """
        self.context = context
        self.request = request

    @view_config(request_method='GET')
    def get_view(self):
        """顯示新增單一頁面的網頁"""
        form = PageForm()
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """新增單一頁面"""
        form = PageForm(self.request.POST)
        if form.validate():
            created_page = DAL.create_page(form)
            if form.attachments.data:
                for each_upload in form.attachments.data:
                    saved_file_name = upload_attachment(each_upload, f'{created_page.id}_')
                    created_page.attachments.append(DAL.create_page_attachment(each_upload.filename, saved_file_name))
            DAL.save_page(created_page)
            return HTTPFound(self.request.route_url('backend_page_list'))
        else:
            return {'form': form}


@view_defaults(route_name='backend_page_list',
               renderer='themes/default/backend/page_list.jinja2',
               permission='view')
class PageListView:
    """顯示單一頁面列表的 view class"""

    def __init__(self, context, request):
        """
        Args:
            context: context 為有註冊帳號才有權限的 acl
            request: pyramid.request.Request
        """
        self.context = context
        self.request = request

    @view_config(request_method='GET')
    def get_view(self):
        """顯示單一頁面的列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        group_id = sanitize_input(self.request.GET.get('g'), int, None)
        page_id = sanitize_input(self.request.GET.get('p', 1), int, 1)
        page_list = DAL.get_page_list(page=page_id, group_id=group_id, quantity_per_page=quantity_per_page)
        return {'page_list': page_list,
                'page_quantity_of_total_pages': DAL.get_page_quantity_of_total_pages(quantity_per_page, group_id),
                'page_id': page_id,
                'quantity_per_page': quantity_per_page}


@view_defaults(route_name='backend_page_delete',
               permission='edit')
class PageDeleteView:
    """刪除單一頁面，只有管理權限的帳號可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的單一頁面"""
        page_id = int(self.request.matchdict['page_id'])
        page = DAL.get_page(page_id)
        if page:
            for each_attachment in page.attachments:
                delete_attachment(each_attachment)
            DAL.delete_page(page)
        return HTTPFound(self.request.route_url('backend_page_list'))


@view_defaults(route_name='backend_page_edit',
               renderer='themes/default/backend/page_edit.jinja2',
               permission='edit')
class PageEditView:

    def __init__(self, context, request):
        """
        Args:
            context: context 為對應的 PageModel
            request: pyramid.request.Request
        """
        self.context = context
        self.request = request

    @view_config(request_method='GET')
    def get_view(self):
        form = PageEditForm()
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in self.context.attachments]
        form.uploaded_attachments.default = [each_attachment.id for each_attachment in self.context.attachments]
        form.process(None, None,
                     title=self.context.title,
                     content=self.context.content,
                     groups=', '.join([each_group.name for each_group in self.context.groups]),
                     tags=', '.join([each_tag.name for each_tag in self.context.tags]))
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        form = PageEditForm()
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in
                                             self.context.attachments]
        form.process(self.request.POST)
        if form.validate():
            page_id = int(self.request.matchdict['page_id'])
            page = DAL.get_page(page_id)
            if page:
                page = DAL.update_page(page, form)

                # 若發現使用者取消勾選已上傳的附件則刪除之
                selected_attachment_ids = form.uploaded_attachments.data
                for each_uploaded_attachment in page.attachments:
                    if each_uploaded_attachment.id not in selected_attachment_ids:
                        DAL.delete_page_attachment(each_uploaded_attachment)
                        delete_attachment(each_uploaded_attachment)

                # 上傳新增的附件
                if form.attachments.data:
                    for each_upload in form.attachments.data:
                        saved_file_name = upload_attachment(each_upload, f'{page.id}_')
                        page.attachments.append(DAL.create_page_attachment(each_upload.filename, saved_file_name))

                DAL.save_page(page)

                return HTTPFound(self.request.route_url('backend_page_list'))
            else:
                self.request.flash('page 物件不存在', 'fail')
        return {'form': form}