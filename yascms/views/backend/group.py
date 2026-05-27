import logging

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden

from yascms.dal import DAL
from yascms.forms.backend.account import GroupCreateForm
from yascms.helpers.backend.group import generate_group_trees
from yascms.enum import GroupType, EmailType


logger = logging.getLogger(__name__)


def check_editing_permission(group_id):
    """根群組與最高管理者群組其 id 為 1 和 2，這兩個群組唯讀不可編輯

    Args:
        request: pyramid.request.Request
        group_id: group id

    Returns:
        如果是內建群組，回傳 HTTPForbidden，否則回傳 None
    """
    if group_id <= 2:
        logger.error('內建根群組/最高管理者群組不可編輯')
        return HTTPForbidden()


@view_defaults(route_name='backend_group_list',
               renderer='',
               permission='view')
class GroupListView:
    """列表使用者群組的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/group_list.jinja2'

    @view_config()
    def get_view(self):
        return {'group_trees': generate_group_trees(), 'GroupType': GroupType, 'EmailType': EmailType}


@view_defaults(route_name='backend_group_create',
               renderer='',
               permission='edit')
class GroupCreateView:
    """建立使用者群組的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/group_create.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = GroupCreateForm()
        return {'form': form,
                'group_trees': generate_group_trees()}

    @view_config(request_method='POST')
    def post_view(self):
        form = GroupCreateForm(self.request.POST)
        valid_primary_email_choices = [each_email['address'] for each_email in form.email.data]
        if valid_primary_email_choices:
            form.primary_email.choices = valid_primary_email_choices
        if form.validate():
            group = DAL.create_group()
            result = self._sync(form, group)
            if result:
                DAL.save_group(group)
                msg = f'{group.name} 群組建立成功'
                logger.info(msg)
                self.request.session.flash(msg, 'success')
                return HTTPFound(location=self.request.route_url('backend_group_list'))
            else:
                msg = 'Email 已存在不可重複'
                logger.info(msg)
                self.request.session.flash(msg, 'fail')
        return {'form': form,
                'group_trees': generate_group_trees()}

    def _sync(self, form, group):
        """將表單的資料同步給 group model

        Args:
            form: wtforms.Form 物件
            group: yascms.models.account.GroupModel

        Returns:
            同步成功回傳 True，失敗回傳 False
        """
        group.name = form.name.data
        email_list = [each_email['address'] for each_email in form.email.data]
        if email_list:
            if not DAL.sync_group_email(group, email_list, form.primary_email.data):
                return False
        group.type = form.type.data
        group.order = form.order.data
        group.ancestor_id = form.ancestor_id.data
        return True


@view_defaults(route_name='backend_group_edit',
               renderer='',
               permission='edit')
class GroupEditView:
    """編輯使用者群組的 view"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'themes/{self.request.effective_theme_name}/backend/group_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        group_id = int(self.request.matchdict['group_id'])
        invalid_permission = check_editing_permission(group_id)
        if invalid_permission:
            return invalid_permission
        group = DAL.get_group(group_id)
        if group:
            primary_email = DAL.get_group_primary_email(group_id)
            form = GroupCreateForm(obj=group)
            if primary_email:
                form.primary_email.data = primary_email
            return {'form': form,
                    'group_trees': generate_group_trees()}
        else:
            logger.error('找不到群組 ID %d', group_id)
            raise HTTPNotFound()
        return HTTPFound(location=self.request.route_url('backend_group_list'))

    @view_config(request_method='POST')
    def post_view(self):
        form = GroupCreateForm(self.request.POST)
        form.primary_email.choices = [each_email['address'] for each_email in form.email.data]
        if form.validate():
            group_id = int(self.request.matchdict['group_id'])
            invalid_permission = check_editing_permission(group_id)
            if invalid_permission:
                return invalid_permission
            group = DAL.get_group(group_id)
            if group:
                result = self._sync(form, group)
                if result:
                    DAL.save_group(group)
                    msg = f'{group.name} 群組修改成功'
                    logger.info(msg)
                    self.request.session.flash(msg, 'success')
                    return HTTPFound(location=self.request.route_url('backend_group_list'))
                else:
                    msg = '設定的 Email 已存在且未關聯至此群組'
                    logger.info(msg)
                    self.request.session.flash(msg, 'fail')
            else:
                logger.error('找不到群組 ID %d', group_id)
                raise HTTPNotFound()
        return {'form': form,
                'group_trees': generate_group_trees()}

    def _sync(self, form, group):
        """將表單的資料同步給 group model

        Args:
            form: wtforms.Form 物件
            group: yascms.models.account.GroupModel

        Returns:
            同步成功回傳 True
        """
        group.name = form.name.data
        email_list = [each_email['address'] for each_email in form.email.data]
        if email_list:
            if not DAL.sync_group_email(group, email_list, form.primary_email.data):
                return False
        group.type = form.type.data
        group.order = form.order.data
        group.ancestor_id = form.ancestor_id.data
        return True


# TODO: 改成用 post 處理刪除
@view_defaults(route_name='backend_group_delete', permission='edit')
class GroupDeleteView:
    """刪除使用者群組的 view"""

    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get_view(self):
        group_id = int(self.request.matchdict['group_id'])
        invalid_permission = check_editing_permission(group_id)
        if invalid_permission:
            return invalid_permission
        group = DAL.get_group(group_id)
        if group:
            DAL.delete_group(group)
            msg = f'{group.name} 群組刪除成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(location=self.request.route_url('backend_group_list'))
        else:
            logger.error('找不到群組 ID %d', group_id)
            raise HTTPNotFound()

