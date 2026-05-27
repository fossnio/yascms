import logging
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from yascms.forms.backend.page import PageForm, PageEditForm
from yascms.helpers import sanitize_input
from yascms.helpers.backend.file import upload_attachment, delete_attachment
from yascms.dal import DAL
from yascms.helpers.backend.group import generate_group_trees


logger = logging.getLogger(__name__)


@view_defaults(route_name='backend_page_create',
               renderer='',
               permission='edit')
class PageCreateView:
    """建立單一頁面的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/page_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示新增單一頁面的網頁"""
        form = PageForm()
        return {'form': form,
                'group_trees': generate_group_trees()}

    @view_config(request_method='POST')
    def post_view(self):
        """新增單一頁面"""
        form = PageForm(self.request.POST)
        form.group_ids.choices = [(each_group.id, each_group.name) for each_group in DAL.get_group_list()]
        if form.validate():
            created_page = DAL.create_page(form)
            if form.attachments.data:
                for each_upload in form.attachments.data:
                    saved_file_name = upload_attachment(each_upload, 'pages', f'{created_page.id}_')
                    created_page.attachments.append(DAL.create_page_attachment(each_upload.filename, saved_file_name))
            DAL.save_page(created_page)
            msg = f'單一頁面 {form.title.data} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_page_list'))
        else:
            return {'form': form, 'group_trees': generate_group_trees()}


@view_defaults(route_name='backend_page_list',
               renderer='',
               permission='view')
class PageListView:
    """顯示單一頁面列表的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/page_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示單一頁面的列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        group_id = sanitize_input(self.request.GET.get('g'), int, None)
        page_number = sanitize_input(self.request.GET.get('p', 1), int, 1)
        page_list = DAL.get_page_list(page_number=page_number, group_id=group_id, quantity_per_page=quantity_per_page)
        return {'page_list': page_list,
                'page_quantity_of_total_pages': DAL.get_page_quantity_of_total_pages(quantity_per_page, group_id),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page}


# TODO: 用 post 處理刪除
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
                delete_attachment(each_attachment.real_name, 'pages')
            DAL.delete_page(page)
            msg = f'單一頁面 {page.title} 刪除成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
        else:
            logger.error('找不到單一頁面 ID %d', page_id)
            raise HTTPNotFound()
        return HTTPFound(self.request.route_url('backend_page_list'))


@view_defaults(route_name='backend_page_edit',
               renderer='',
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
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/page_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = PageEditForm()
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in self.context.attachments]
        form.uploaded_attachments.default = [each_attachment.id for each_attachment in self.context.attachments]
        group_ids = [each_group.id for each_group in self.context.groups]
        form.process(None, None,
                     title=self.context.title,
                     content=self.context.content,
                     group_ids=group_ids,
                     tags=', '.join([each_tag.name for each_tag in self.context.tags]))
        return {'form': form,
                'group_ids': group_ids,
                'group_trees': generate_group_trees()}

    @view_config(request_method='POST')
    def post_view(self):
        form = PageEditForm()
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in
                                             self.context.attachments]
        form.group_ids.choices = [(each_group.id, each_group.name) for each_group in DAL.get_group_list()]
        form.process(self.request.POST)
        if form.validate():
            page_id = int(self.request.matchdict['page_id'])
            page = DAL.get_page(page_id)
            if page:
                page = DAL.update_page(page, form, self.request.session['is_admin'])

                # 若發現使用者取消勾選已上傳的附件則刪除之
                selected_attachment_ids = form.uploaded_attachments.data
                for each_uploaded_attachment in page.attachments:
                    if each_uploaded_attachment.id not in selected_attachment_ids:
                        DAL.delete_page_attachment(each_uploaded_attachment)
                        delete_attachment(each_uploaded_attachment.real_name, 'pages')

                # 上傳新增的附件
                if form.attachments.data:
                    for each_upload in form.attachments.data:
                        saved_file_name = upload_attachment(each_upload, 'pages', f'{page.id}_')
                        page.attachments.append(DAL.create_page_attachment(each_upload.filename, saved_file_name))

                DAL.save_page(page)
                msg = f'單一頁面 {page.title} 更新成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_page_list'))
            else:
                logger.error('找不到單一頁面 ID %d', page_id)
                raise HTTPNotFound()
        return {'form': form,
                'group_ids': form.group_ids.data,
                'group_trees': generate_group_trees()}
