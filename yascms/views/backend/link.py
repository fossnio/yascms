import logging

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from yascms.forms.backend.link import LinkForm, LinkCategoryForm
from yascms.dal import DAL
from yascms.helpers import sanitize_input
from yascms.helpers.backend.file import upload_attachment, delete_attachment


logger = logging.getLogger(__name__)


@view_defaults(route_name='backend_link_create', renderer='', permission='edit')
class LinkCreateView:
    """建立好站連結的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立好站連結表單"""
        form = LinkForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                         DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_link_category_list()]
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """處理建立好站連結的表單"""
        form = LinkForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_link_category_list()]
        form.process(self.request.POST)
        if form.validate():
            created_link = DAL.create_link(form)
            # 上傳圖檔並將相關資料寫入資料庫
            if form.icon.data:
                created_link.icon = upload_attachment(form.icon.data, 'links', f'{created_link.id}_', need_resize=True)
            DAL.save_link(created_link)
            msg = f'好站連結 {created_link.title} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_link_list'))
        return {'form': form}


@view_defaults(route_name='backend_link_list', renderer='', permission='view')
class LinkListView:
    """顯示好站連結的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示好站連結的列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        category_id = sanitize_input(self.request.GET.get('c'), int, None)
        page_number = sanitize_input(self.request.GET.get('p', 1), int, 1)
        link_list = DAL.get_link_list(page_number=page_number, quantity_per_page=quantity_per_page, category_id=category_id)
        return {'link_list': link_list,
                'page_quantity_of_total_links': DAL.get_page_quantity_of_total_links(quantity_per_page, category_id),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page}


# TODO: 要把刪除改成 post 處理
@view_defaults(route_name='backend_link_delete',
               permission='edit')
class LinkDeleteView:
    """刪除最新消息，只有管理者與最新消息所屬群組可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的好站連結"""
        link_id = int(self.request.matchdict['link_id'])
        link = DAL.get_link(link_id)
        if link:
            delete_attachment(link.icon, 'links')
            DAL.delete_link(link)
            msg = f'好站連結 {link.title} 刪除成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_link_list'))
        else:
            logger.error('找不到好站連結 ID %d', link_id)
            raise HTTPNotFound()


@view_defaults(route_name='backend_link_edit',
               renderer='',
               permission='edit')
class LinkEditView:

    def __init__(self, context, request):
        """
        Args:
            context: context 為對應的 LinkModel
            request: pyramid.request.Request
        """
        self.context = context
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = LinkForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.group_id.default = self.context.group.id
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_link_category_list()]
        form.category_id.default = self.context.category.id
        form.is_pinned.default = True if self.context.is_pinned else False
        form.process(None, None,
                     title=self.context.title,
                     url=self.context.url)
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        form = LinkForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_link_category_list()]
        form.process(self.request.POST)
        if form.validate():
            link_id = int(self.request.matchdict['link_id'])
            link = DAL.get_link(link_id)
            if link:
                link = DAL.update_link(link, form)
                # 若使用者又傳了圖檔，則無條件蓋掉
                if form.icon.data:
                    delete_attachment(link.icon, 'links')
                    link.icon = upload_attachment(form.icon.data, 'links', f'{link.id}_')
                DAL.save_link(link)
                msg = f'好站連結 {link.title} 修改成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_link_list'))
            else:
                logger.error('找不到好站連結 ID %d', link_id)
                raise HTTPNotFound()
        return {'form': form}


@view_defaults(route_name='backend_link_category_create', renderer='', permission='edit')
class LinkCategoryCreateView:
    """建立好站連結分類的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_category_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立好站連結分類表單"""
        form = LinkCategoryForm()
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """處理建立好站連結分類的表單"""
        form = LinkCategoryForm(self.request.POST)
        if form.validate():
            DAL.create_link_category(form)
            msg = f'好站連結分類 {form.name} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_link_category_list'))
        return {'form': form}


@view_defaults(route_name='backend_link_category_list', renderer='', permission='edit')
class LinkCategoryListView:
    """顯示好站連結列表"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_category_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示好站連結列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        page_number = sanitize_input(self.request.GET.get('p', 1), int, 1)
        return {'link_category_list': DAL.get_link_category_list(),
                'page_quantity_of_total_link_categories': DAL.get_page_quantity_of_total_link_categories(quantity_per_page),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page}


# TODO: 改成用 post 處理刪除
@view_defaults(route_name='backend_link_category_delete',
               permission='edit')
class LinkCategoryDeleteView:
    """刪除好站連結分類，只有管理者可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的好站連結分類"""
        link_category_id = int(self.request.matchdict['link_category_id'])
        if not DAL.delete_link_category(link_category_id):
            msg = f'好站連結分類 ID {link_category_id} 刪除失敗，請確認是否還有相依的好站連結'
            logger.warning(msg)
            self.request.session.flash(msg, 'fail')
        return HTTPFound(self.request.route_url('backend_link_category_list'))


@view_defaults(route_name='backend_link_category_edit', renderer='', permission='edit')
class LinkCategoryEditView:
    """編輯好站連結分類的 view"""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/link_category_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立好站連結分類表單"""
        link_category_id = int(self.request.matchdict['link_category_id'])
        link_category = DAL.get_link_category(link_category_id)
        if link_category:
            form = LinkCategoryForm(obj=link_category)
            return {'form': form}
        else:
            logger.error('找不到好站連結分類 ID %d', link_category_id)
            raise HTTPNotFound()

    @view_config(request_method='POST')
    def post_view(self):
        """編輯好站連結分類的表單"""
        link_category_id = int(self.request.matchdict['link_category_id'])
        link_category = DAL.get_link_category(link_category_id)
        if link_category:
            form = LinkCategoryForm(self.request.POST)
            if form.validate():
                DAL.update_link_category(link_category, form)
                msg = f'好站連結分類 {link_category.name} 更新成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_link_category_list'))
            else:
                return {'form': form}
        else:
            logger.error('找不到好站連結分類 ID %d', link_category_id)
            raise HTTPNotFound()
