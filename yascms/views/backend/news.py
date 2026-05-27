import logging
import datetime

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden

from yascms.forms.backend.news import NewsForm, NewsEditForm, NewsCategoryForm
from yascms.dal import DAL
from yascms.helpers import sanitize_input
from yascms.helpers.backend.file import upload_attachment, delete_attachment


logger = logging.getLogger(__name__)


@view_defaults(route_name='backend_news_create', renderer='', permission='edit')
class NewsCreateView:
    """建立最新消息的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立最新消息表單"""
        form = NewsForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                        for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                         DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_news_category_list()]
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """處理建立最新消息的表單"""
        form = NewsForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_news_category_list()]
        form.process(self.request.POST)
        if form.validate():
            created_news = DAL.create_news(form)
            # 先上傳檔案再將檔案相關資料寫入資料庫
            if form.attachments.data:
                for each_upload in form.attachments.data:
                    now = datetime.datetime.now()
                    saved_file_name = upload_attachment(each_upload, now.strftime('news/%Y/%m'), f'{created_news.id}_')
                    created_news.attachments.append(DAL.create_news_attachment(each_upload.filename, saved_file_name))
            DAL.save_news(created_news)
            msg = f'最新消息 {created_news.title} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_news_list'))
        return {'form': form}


@view_defaults(route_name='backend_news_list', renderer='', permission='view')
class NewsListView:
    """顯示最新消息列表的 view class"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示最新消息的列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        category_id = sanitize_input(self.request.GET.get('c'), int, None)
        page_number = sanitize_input(self.request.GET.get('p', 1), int, 1)
        search_key = sanitize_input(self.request.GET.get('k', ''), str, '')
        search_value = sanitize_input(self.request.GET.get('v', ''), str, '')
        if search_key.strip() != '':
            if search_key not in ('publisher', 'title', 'content'):
                raise HTTPNotFound()
            if search_value.strip() == '':
                raise HTTPNotFound()
        news_list = DAL.get_backend_news_list(page_number, quantity_per_page, category_id, search_key, search_value)
        return {'news_list': news_list,
                'today': datetime.date.today(),
                'now': datetime.datetime.now(),
                'page_quantity_of_total_news': DAL.get_page_quantity_of_total_news(quantity_per_page, category_id,
                                                                                   False, search_key, search_value),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page}


# TODO: 改成用 post 處理刪除
@view_defaults(route_name='backend_news_delete',
               permission='edit')
class NewsDeleteView:
    """刪除最新消息，只有管理者與最新消息所屬群組可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的最新消息"""
        news_id = int(self.request.matchdict['news_id'])
        news = DAL.get_news(news_id)
        if news:
            for each_attachment in news.attachments:
                delete_attachment(each_attachment.real_name, news.publication_datetime.strftime('news/%Y/%m'))
            DAL.delete_news(news)
            msg = f'最新消息 {news.title} 刪除成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
        else:
            logger.error('找不到最新消息 ID %d', news_id)
            raise HTTPNotFound()
        return HTTPFound(self.request.route_url('backend_news_list'))


@view_defaults(route_name='backend_news_edit',
               renderer='',
               permission='edit')
class NewsEditView:

    def __init__(self, context, request):
        """
        Args:
            context: context 為對應的 NewsModel
            request: pyramid.request.Request
        """
        self.context = context
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = NewsEditForm()
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in self.context.attachments]
        form.uploaded_attachments.default = [each_attachment.id for each_attachment in self.context.attachments]
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                        for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.group_id.default = self.context.group.id
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_news_category_list()]
        form.category_id.default = self.context.category.id
        form.is_pinned.default = True if self.context.is_pinned else False
        form.process(None, None,
                     title=self.context.title,
                     content=self.context.content,
                     pinned_start_datetime=self.context.pinned_start_datetime,
                     pinned_end_datetime=self.context.pinned_end_datetime,
                     visible_start_datetime=self.context.visible_start_datetime,
                     visible_end_datetime=self.context.visible_end_datetime,
                     tags=', '.join([each_tag.name for each_tag in self.context.tags]))
        return {'form': form, 'news': self.context}

    @view_config(request_method='POST')
    def post_view(self):
        form = NewsEditForm()
        if self.request.session['is_admin']:
            form.group_id.choices = [(each_group.id, f'{each_group.name} (上層 {each_group.ancestor.name})')
                                     for each_group in DAL.get_group_list() if each_group.ancestor]
        else:
            form.group_id.choices = [(each_staff_group.id, each_staff_group.name) for each_staff_group in
                                     DAL.get_staff_group_list(self.request.session['user_id'])]
        form.category_id.choices = [(category.id, category.name) for category in DAL.get_news_category_list()]
        form.uploaded_attachments.choices = [(each_attachment.id, each_attachment.original_name) for each_attachment in
                                             self.context.attachments]
        form.process(self.request.POST)
        if form.validate():
            news_id = int(self.request.matchdict['news_id'])
            news = DAL.get_news(news_id)
            if news:
                news = DAL.update_news(news, form)

                # 若發現使用者取消勾選已上傳的附件則刪除之
                selected_attachment_ids = form.uploaded_attachments.data
                for each_uploaded_attachment in news.attachments:
                    if each_uploaded_attachment.id not in selected_attachment_ids:
                        DAL.delete_news_attachment(each_uploaded_attachment)
                        delete_attachment(each_uploaded_attachment.real_name, news.publication_datetime.strftime('news/%Y/%m'))

                # 上傳新增的附件
                if form.attachments.data:
                    for each_upload in form.attachments.data:
                        now = datetime.datetime.now()
                        saved_file_name = upload_attachment(each_upload, now.strftime('news/%Y/%m'), f'{news.id}_')
                        news.attachments.append(DAL.create_news_attachment(each_upload.filename, saved_file_name))

                DAL.save_news(news)
                msg = f'最新消息 {news.title} 更新成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_news_list'))
            else:
                logger.error('找不到最新消息 ID %d', news_id)
                raise HTTPNotFound()
        return {'form': form}


@view_defaults(route_name='backend_news_category_create', renderer='', permission='edit')
class NewsCategoryCreateView:
    """建立最新消息分類的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_category_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立最新消息分類表單"""
        form = NewsCategoryForm()
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        """處理建立最新消息分類的表單"""
        form = NewsCategoryForm(self.request.POST)
        if form.validate():
            DAL.create_news_category(form)
            msg = f'最新消息分類 {form.name.data} 建立成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(self.request.route_url('backend_news_category_list'))
        return {'form': form}


@view_defaults(route_name='backend_news_category_list', renderer='', permission='edit')
class NewsCategoryListView:
    """顯示最新消息列表"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_category_list.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """顯示最新消息列表"""
        quantity_per_page = sanitize_input(self.request.GET.get('q', 20), int, 20)
        page_number = sanitize_input(self.request.GET.get('p', 1), int, 1)
        return {'news_category_list': DAL.get_news_category_list(),
                'page_quantity_of_total_news_categories': DAL.get_page_quantity_of_total_news_categories(quantity_per_page),
                'page_number': page_number,
                'quantity_per_page': quantity_per_page}


# TODO: 換用 post 處理 delete
@view_defaults(route_name='backend_news_category_delete',
               permission='edit')
class NewsCategoryDeleteView:
    """刪除最新消息分類，只有管理者可刪"""

    def __init__(self, request):
        """
        Args:
            request: pyramid.request.Request
        """
        self.request = request

    @view_config()
    def delete_view(self):
        """刪除指定的最新消息分類"""
        news_category_id = int(self.request.matchdict['news_category_id'])
        if not DAL.delete_news_category(news_category_id):
            msg = f'最新消息分類 ID {news_category_id} 刪除失敗，請確認是否還有相依的最新消息'
            logger.warning(msg)
            self.request.session.flash(msg, 'fail')
        msg = f'最新消息分類 ID {news_category_id} 刪除成功'
        logger.info(msg)
        self.request.session.flash(msg, 'success')
        return HTTPFound(self.request.route_url('backend_news_category_list'))


@view_defaults(route_name='backend_news_category_edit', renderer='', permission='edit')
class NewsCategoryEditView:
    """編輯最新消息分類的 view"""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/news_category_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        """產生建立最新消息分類表單"""
        news_category_id = int(self.request.matchdict['news_category_id'])
        news_category = DAL.get_news_category(news_category_id)
        if news_category:
            form = NewsCategoryForm(obj=news_category)
            return {'form': form}
        else:
            logger.error('找不到最新消息分類 ID %d', news_category_id)
            raise HTTPNotFound()

    @view_config(request_method='POST')
    def post_view(self):
        """編輯最新消息分類的表單"""
        news_category_id = int(self.request.matchdict['news_category_id'])
        news_category = DAL.get_news_category(news_category_id)
        if news_category:
            form = NewsCategoryForm(self.request.POST)
            if form.validate():
                DAL.update_news_category(news_category, form)
                msg = f'最新消息分類 {news_category.name} 更新成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(self.request.route_url('backend_news_category_list'))
            else:
                return {'form': form}
        else:
            logger.error('找不到最新消息分類 ID %d', news_category_id)
            raise HTTPNotFound()
