"""資料庫存取抽象層

為了避免 views 相依 orm 操作，所以抽象資料存取層
"""
import json
import math
import string
import random
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from pyramid_sqlalchemy import Session as DBSession

from yascms.models.account import UserModel, GroupModel
from yascms.models.news import NewsModel, NewsCategoryModel, NewsAttachmentModel
from yascms.models.navbar import NavbarModel
from yascms.models.global_config import GlobalConfigModel
from yascms.models.page import PageModel, PageAttachmentModel
from yascms.models.tag import TagModel
from yascms.models.link import LinkModel, LinkCategoryModel
from yascms.models.telext import TelExtModel
from yascms.models.theme_config import ThemeConfigModel
from yascms.models.auth_log import AuthLogModel
from yascms.models.account import EmailModel
from yascms.models.api_token import APITokenModel
from yascms.enum import GroupType, NavbarType, EmailType, PinnedType, AuthLogType, NavbarLeafNodeType
from yascms.exceptions import TpYassError


logger = logging.getLogger(__name__)


class DAL:

    @staticmethod
    def auth_user(account, password):
        """根據傳入的帳號密碼找到對應的紀錄並回傳

        Args:
            account: 帳號名稱
            password: 密碼

        Returns:
            回傳 user model
        """
        user = DBSession.query(UserModel).filter_by(account=account).one_or_none()
        if user and user.verify_password(password):
            return user

    @staticmethod
    def get_frontend_news_list(page_number=1, quantity_per_page=20, category_id=None):
        """傳回 frontend 會用到的最新消息列表，包含置頂與非置頂。

        一般傳回資料，都是根據傳入的頁數與每頁的數量，來計算要傳回去的資料。但我這邊故意設計成只有第1頁才可以回傳置頂的最新消息，
        而且置頂的最新消息，不算在每頁的數量裡面。

        舉個例子：假設現在置頂有 10 筆，然後設定值為每一頁有 20 筆。那這樣第一頁就會有 10 + 20 = 30 筆最新消息，
        第二頁以後才會恢復成每一頁 20 筆。

        這樣的設計，可以讓想長期置頂的需求可以滿足，又不會因此遮蓋到沒有置頂的最新消息顯示的空間。

        Args:
            page_number: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            category_id: 指定要撈取的最新消息分類，None 代表不指定

        Returns:
            回傳最新消息列表
        """
        results = []
        now = datetime.now()

        # 第一頁要先撈設為置頂、置頂時間有效且顯示時間有效的最新消息
        if page_number == 1:
            pinned_results = DBSession.query(NewsModel)
            if category_id:
                pinned_results = pinned_results.filter_by(category_id=category_id)
            pinned_results = pinned_results.filter(NewsModel.is_pinned == PinnedType.IS_PINNED.value)
            pinned_results = (pinned_results.filter(now >= NewsModel.pinned_start_datetime,
                                                    now < NewsModel.pinned_end_datetime)
                              .filter(or_(NewsModel.visible_start_datetime.is_(None),
                                                        now >= NewsModel.visible_start_datetime))
                              .filter(or_(NewsModel.visible_end_datetime.is_(None),
                                          now < NewsModel.visible_end_datetime)))
            results.extend(pinned_results.order_by(NewsModel.viewable_datetime.desc(), NewsModel.id.desc()).all())

        # 撈出沒有設定置頂的、或是有設定置頂但置頂時間已經超過的最新消息
        unpinned_results = DBSession.query(NewsModel)
        if category_id:
            unpinned_results = unpinned_results.filter_by(category_id=category_id)
        unpinned_results = unpinned_results.filter(or_(and_(NewsModel.is_pinned == PinnedType.IS_NOT_PINNED.value,
                                                            or_(NewsModel.visible_start_datetime.is_(None),
                                                                now >= NewsModel.visible_start_datetime),
                                                            or_(NewsModel.visible_end_datetime.is_(None),
                                                                now < NewsModel.visible_end_datetime)),
                                                       and_(NewsModel.is_pinned == PinnedType.IS_PINNED.value,
                                                            or_(now < NewsModel.pinned_start_datetime,
                                                                now >= NewsModel.pinned_end_datetime),
                                                            or_(NewsModel.visible_start_datetime.is_(None),
                                                                now >= NewsModel.visible_start_datetime),
                                                            or_(NewsModel.visible_end_datetime.is_(None),
                                                                now < NewsModel.visible_end_datetime))))
        results.extend(unpinned_results.order_by(NewsModel.viewable_datetime.desc(), NewsModel.id.desc())
                                       .limit(quantity_per_page)
                                       .offset((page_number-1)*quantity_per_page))
        return results

    @staticmethod
    def get_backend_news_list(page_number=1, quantity_per_page=20, category_id=None, search_key=None, search_value=None):
        """傳回 backend 會用到的最新消息列表，置頂的不用特別放在最上面，按照 id 反向排序即可

        Args:
            page_number: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            category_id: 指定要撈取的最新消息分類，None 代表不指定
            search_key: 搜尋條件
            search_value: 搜尋內容

        Returns:
            回傳最新消息列表
        """
        results = DBSession.query(NewsModel)
        if search_key and search_value:
            if search_key == 'publisher':
                results = results.join(GroupModel).filter(GroupModel.name.like(f'%{search_value}%'))
            elif search_key == 'title':
                results = results.filter(NewsModel.title.like(f'%{search_value}%'))
            else:
                results = results.filter(NewsModel.content.like(f'%{search_value}%'))
        if category_id:
            results.filter_by(category_id=category_id)
        return results.order_by(NewsModel.id.desc()).limit(quantity_per_page).offset((page_number-1)*quantity_per_page)

    @staticmethod
    def get_news_category_list():
        """回傳最新消息分類列表"""
        return DBSession.query(NewsCategoryModel).order_by(NewsCategoryModel.order)

    @staticmethod
    def get_page_quantity_of_total_news(quantity_per_page, category_id=None, unpinned_only=True,
                                        search_key=None, search_value=None):
        """回傳最新消息總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息
            category_id: 若有指定，則只會傳回符合此分類的最新消息頁數
            unpinned_only: 是否只計算非有效置頂期限的最新消息筆數，若為 False 則計算 "所有" 最新消息的筆數
            search_key: 搜尋條件
            search_value: 搜尋內容

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(NewsModel.id))
        if search_key and search_value:
            if search_key == 'publisher':
                results = results.join(GroupModel).filter(GroupModel.name.like(f'%{search_value}%'))
            elif search_key == 'title':
                results = results.filter(NewsModel.title.like(f'%{search_value}%'))
            else:
                results = results.filter(NewsModel.content.like(f'%{search_value}%'))
        now = datetime.now()
        if category_id:
            results = results.filter_by(category_id=category_id)
        if unpinned_only:
            results = results.filter(or_(and_(NewsModel.is_pinned == PinnedType.IS_NOT_PINNED.value,
                                              or_(NewsModel.visible_start_datetime.is_(None),
                                                  now >= NewsModel.visible_start_datetime),
                                              or_(NewsModel.visible_end_datetime.is_(None),
                                                  now < NewsModel.visible_end_datetime)),
                                         and_(NewsModel.is_pinned == PinnedType.IS_PINNED.value,
                                              or_(now < NewsModel.pinned_start_datetime,
                                                  now >= NewsModel.pinned_end_datetime),
                                              or_(NewsModel.visible_start_datetime.is_(None),
                                                  now >= NewsModel.visible_start_datetime),
                                              or_(NewsModel.visible_end_datetime.is_(None),
                                                  now < NewsModel.visible_end_datetime))))
        return math.ceil(results.scalar()/quantity_per_page)

    @staticmethod
    def get_site_config_list():
        """傳回系統相關的設定檔，都是以 site_ 開頭的"""
        config_list = (DBSession.query(GlobalConfigModel)
                                .filter(GlobalConfigModel.name.startswith('site_'))
                                .all())
        results = []
        for each_config in config_list:
            if each_config.type == 'int':
                normalized_value = int(each_config.value)
            elif each_config.type == 'bool':
                if each_config.value == 'True':
                    normalized_value = True
                else:
                    normalized_value = False
            else:
                normalized_value = each_config.value
            results.append(SimpleNamespace(id=each_config.id, name=each_config.name, value=normalized_value,
                                           type=each_config.type, description=each_config.description))
        return results

    @staticmethod
    def get_oauth2_integration_config():
        """傳回系統支援的 OAuth2 Providers 的列表"""
        return json.loads(DBSession.query(GlobalConfigModel.value).filter_by(name='oauth2_integration').scalar())

    @staticmethod
    def save_oauth2_integration_config(config):
        """儲存 OAuth2 整合的設定

        Args:
            config: OAuth2 的整合設定

        Returns:
            儲存成功回傳 True
        """
        (DBSession.query(GlobalConfigModel)
         .filter_by(name='oauth2_integration')
         .update({GlobalConfigModel.value: json.dumps(config, ensure_ascii=False)}))
        return True

    @staticmethod
    def get_available_theme_name_list():
        """回傳目前可用的樣板名稱列表

        Returns:
            樣板名稱列表
        """
        return [each_theme.name for each_theme in DBSession.query(ThemeConfigModel.name)]

    @staticmethod
    def get_current_theme_name():
        """回傳目前使用的樣板名稱

        Returns:
            回傳目前的樣板名稱
        """
        return DBSession.query(GlobalConfigModel.value).filter_by(name='theme_name').one().value

    @staticmethod
    def set_current_theme_name(theme_name):
        """設定目前使用的樣板名稱

        Args:
            theme_name: 設定成預設的樣板名稱

        Returns:
            成功回傳 True
        """
        DBSession.query(GlobalConfigModel).filter_by(name='theme_name').update({GlobalConfigModel.value: theme_name})
        return True

    @staticmethod
    def get_theme_config_list():
        """回傳所有樣板名稱列表

        Returns:
            樣板名稱列表
        """
        return DBSession.query(ThemeConfigModel.id, ThemeConfigModel.name)

    @staticmethod
    def get_theme_config(theme_name):
        """根據傳入的 theme_name 傳回佈景主題設定檔

        Args:
            theme_name: 佈景主題的名稱

        Returns:
            佈景主題設定資料結構，會將存在資料庫中的 json 格式轉成 python 的資料型別
        """
        return json.loads((DBSession.query(ThemeConfigModel)
                                    .filter_by(name=theme_name)
                                    .one()).value)

    @staticmethod
    def update_theme_config(theme_config):
        """更新指定的 theme_confg

        Args:
            theme_config: 樣板設定資料結構

        Returns:
            儲存成功則回傳 True
        """
        (DBSession.query(ThemeConfigModel)
                  .filter_by(name=theme_config['name'])
                  .update({ThemeConfigModel.value: json.dumps(theme_config, ensure_ascii=False)}))
        return True

    @staticmethod
    def add_theme_config(config):
        """將傳入的 config 資料結構直接存入 theme_config 資料表

        Args:
            config: 設定檔的資料結構，由樣板自帶的 config.json 藉由 json.loads 轉換而成

        Returns:
            None
        """
        theme_config = ThemeConfigModel(name=config['name'], value=json.dumps(config, ensure_ascii=False))
        DBSession.add(theme_config)

    @staticmethod
    def delete_theme_config(theme_name):
        """根據傳入的樣板名稱刪除該樣板的設定

        Args:
            theme_name: 樣板名稱

        Returns:
            成功回傳 True
        """
        DBSession.query(ThemeConfigModel).filter_by(name=theme_name).delete()
        return True

    @staticmethod
    def create_user():
        """建立使用者物件並回傳

        Returns:
            回傳使用者物件
        """
        return UserModel()

    @staticmethod
    def get_user_account(account):
        """根據傳入的使用者帳號找到該物件並回傳

        Args:
            account: 使用者帳號名稱

        Returns:
            回傳使用者物件
        """
        return DBSession.query(UserModel).filter_by(account=account).one_or_none()

    @staticmethod
    def get_user_from_email(address):
        """根據傳入的 email 位址找到對應的使用者並回傳

        Args:
            address: 使用者 email 位址

        Returns:
            成功則回傳使用者物件，否則回傳 None
        """
        email = DBSession.query(EmailModel).filter_by(address=address).one_or_none()
        if email:
            return email.user
        else:
            return None

    @staticmethod
    def get_user(user_id):
        """取得使用者物件並回傳

        Args:
            user_id: UserModel.id

        Returns:
            回傳使用者物件
        """
        return DBSession.get(UserModel, user_id)

    @staticmethod
    def get_user_primary_email(user_id):
        """取得使用者的主要 email 位址

        Args:
            user_id: UserModel primary key

        Returns:
            回傳使用者的主要 email 位址
        """
        return DBSession.query(EmailModel.address).filter(EmailModel.user_id==user_id,
                                                          EmailModel.type==EmailType.USER_PRIMARY.value).scalar()

    @staticmethod
    def get_users_qty():
        """取得使用者總數並回傳

        Returns:
            回傳使用者總數
        """
        return DBSession.query(func.count(UserModel.id)).scalar()

    @staticmethod
    def sync_user_email(user, email_list, primary_email):
        """將傳入的 email_list 同步至該使用者的 email

        Args:
            user: user model
            email_list: email 位址的 list
            primary_email: 主要 email

        Returns:
            成功回傳 True，失敗回傳 False
        """
        email_model_list = DBSession.query(EmailModel).filter(EmailModel.address.in_(email_list)).all()
        if user.id:
            # 撈回來的 email "必須" 是關聯到這位使用者帳號
            for each_email_model in email_model_list:
                if each_email_model.user_id != user.id:
                    return False
        else:
            # 新建的使用者，理論上資料庫不該撈回任何東西，否則就代表會改到資料庫現有的紀錄
            if email_model_list:
                return False

        email_address_list = [each_email_model.address for each_email_model in email_model_list]

        for each_email in email_list:
            if each_email not in email_address_list:
                email_model_list.append(EmailModel(address=each_email))

        for each_email_model in email_model_list:
            if each_email_model.address == primary_email:
                each_email_model.type = EmailType.USER_PRIMARY.value
            else:
                each_email_model.type = EmailType.USER_SECONDARY.value
        user.email = email_model_list
        DBSession.add(user)
        return True

    @staticmethod
    def save_user(user):
        """將 UserModel 物件存至 DB

        Args:
            user: UserModel 實體

        Returns:
            None
        """
        DBSession.add(user)

    @staticmethod
    def delete_user(user):
        """將 UserModel 物件刪除

        Args:
            user: UserModel 實體

        Returns:
            None
        """
        DBSession.delete(user)

    @staticmethod
    def get_group_list():
        """傳回使用者的群組列表

        排序的依據讓上層的群組排序在前面，然後同一個父群組的群組排在一起，
        再來才是以 order 為排序依據，這樣在 view 的階段就不用再特別處理排序
        """
        return DBSession.query(GroupModel).order_by(GroupModel.depth, GroupModel.ancestor_id, GroupModel.order).all()

    @staticmethod
    def get_staff_group_list(user_id):
        """取得指定 user id 的所屬行政群組 (group type 為 yascms.enum.GroupType.STAFF)。最高管理者也視做是行政群組

        Args:
            user_id: UserModel 的 primary key

        Returns:
            回傳行政群組列表
        """
        return (DBSession.query(GroupModel)
                         .join(UserModel, GroupModel.users)
                         .filter(UserModel.id==user_id, GroupModel.type.in_((GroupType.ADMIN.value, GroupType.STAFF.value))))

    @staticmethod
    def get_groups(group_id_list):
        """根據傳入的 group id 列表回傳多個群組物件

        Args:
            group_id_list: 包含 GroupModel.id 的 list

        Returns:
            回傳符合的群組物件列表
        """

        return DBSession.query(GroupModel).filter(GroupModel.id.in_(group_id_list)).all()

    @staticmethod
    def get_group(group_id):
        """根據傳入的 group_id 回傳群組物件

        Args:
            group_id: 群組的 pk

        Returns:
            回傳群組物件或 None
        """
        return DBSession.get(GroupModel, group_id)

    @staticmethod
    def get_groups_qty():
        """取得群組總數並回傳

        Returns:
            回傳群組總數
        """
        return DBSession.query(func.count(GroupModel.id)).scalar()

    @staticmethod
    def get_group_primary_email(group_id):
        """取得群組主要 email 位址

        Args:
            group_id: GroupModel primary key

        Returns:
            回傳群組的主要 email 位址或 None
        """
        return DBSession.query(EmailModel.address).filter(EmailModel.group_id==group_id,
                                                          EmailModel.type==EmailType.GROUP_PRIMARY.value).scalar()

    @staticmethod
    def sync_group_email(group, email_list, primary_email):
        """將傳入的 email_list 同步至該群組的 email

        Args:
            group: group model
            email_list: email 位址的 list
            primary_email: 主要 email

        Returns:
            成功回傳 True，失敗回傳 False
        """
        email_model_list = DBSession.query(EmailModel).filter(EmailModel.address.in_(email_list)).all()
        if group.id:
            # 撈回來的 email "必須" 是關聯到這群組
            for each_email_model in email_model_list:
                if each_email_model.group_id != group.id:
                    return False
        else:
            # 新建的群組，理論上資料庫不該撈回任何東西，否則就代表會改到資料庫現有的紀錄
            if email_model_list:
                return False

        email_address_list = [each_email_model.address for each_email_model in email_model_list]

        for each_email in email_list:
            if each_email not in email_address_list:
                email_model_list.append(EmailModel(address=each_email))

        for each_email_model in email_model_list:
            if each_email_model.address == primary_email:
                each_email_model.type = EmailType.GROUP_PRIMARY.value
            else:
                each_email_model.type = EmailType.GROUP_SECONDARY.value
        group.email = email_model_list
        DBSession.add(group)
        return True

    @staticmethod
    def get_group_by_name(name):
        """根據傳入的群組名稱回傳對應的群組物件

        Args:
            name: 群組名稱

        Returns:
            回傳群組物件
        """
        return DBSession.query(GroupModel).filter_by(name=name).one_or_none()

    @staticmethod
    def get_or_create_group(name):
        """根據傳入的群組名稱，回傳或建立該群組

        Args:
            name: 群組名稱

        Returns:
            回傳已存在或新建立的群組
        """
        group = DAL.get_group_by_name(name)
        if not group:
            group = GroupModel(name=name)
        return group

    @staticmethod
    def create_group():
        """建立 GroupModel 實體

        Returns:
            GroupModel 實體
        """
        return GroupModel()

    @staticmethod
    def _update_depth_recursively(group, depth):
        """將傳入的 group 群組其 depth 值更新
        並遞迴地處理其下的所有樹狀子群組 depth 值

        Args:
            group: GroupModel 實體

        Returns:
            成功更新完成則回傳 True
        """
        group.depth = depth
        #DBSession.add(group)
        for each_descendant in group.descendants:
            DAL._update_depth_recursively(each_descendant, depth + 1)
        return True

    @staticmethod
    def save_group(group):
        """將 GroupModel 物件存至 DB

        Args:
            group: GroupModel 實體

        Returns:
            None
        """
        DAL._update_depth_recursively(group, DBSession.get(GroupModel, group.ancestor_id).depth + 1)
        DBSession.add(group)

    @staticmethod
    def delete_group(group):
        """刪除指定的 group

        Args:
            group: group 物件
        """
        ancestor_group = group.ancestor
        for each_descendant in list(group.descendants):
            # 將原本 group 的子群組往上移一層
            each_descendant.ancestor = ancestor_group
            # 因為當前的 group 即將被刪掉，要將所有樹狀子群組的 depth - 1 才符合子群組被上移一層的狀態
            DAL._update_depth_recursively(each_descendant, group.depth)
            DBSession.add(each_descendant)
        DBSession.delete(group)

    @staticmethod
    def get_user_list(page=1, quantity_per_page=20, group_id=None):
        """傳回使用者列表

        Args:
            page: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            group_id: 指定要撈取的使用者群組，None 代表不指定

        Returns:
            回傳使用者列表
        """
        results = DBSession.query(UserModel)
        if group_id:
            results = results.filter_by(group_id=group_id)
        return (results.order_by(UserModel.id.desc())
                   [(page-1)*quantity_per_page : (page-1)*quantity_per_page+quantity_per_page])

    @staticmethod
    def get_page_quantity_of_total_users(quantity_per_page, group_id=None):
        """回傳使用者列表總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息
            group_id: 若有指定，則只會傳回符合此群組的使用者頁數

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(UserModel.id))
        if group_id:
            results = results.filter_by(group_id=group_id)
        return math.ceil(results.scalar()/quantity_per_page)

    @staticmethod
    def get_navbar_list(type='all', visible_only=False, excluded_id=None):
        """傳回導覽列列表

        排序的依據讓同一個父群組的群組排在一起，再來才是以 order 為排序依據，這樣在 view 的階段就不用再特別處理排序

        Args:
            type: 產生的 navbar list 類型，若為 intermediate 則只傳回可接受子選單的選單物件，若為 all 則回傳全部
            visible_only: 是否只擷取 is_visible 為 True 的導覽列，預設行為是全部擷取
            excluded_id: 用來排除指定的 navbar 物件，避免後台產生建立導覽列樹狀的顯示列表時讓 UI 產生自己的上層可以指給自己的錯誤

        Returns:
            回傳排序後的 navbar list
        """
        results = DBSession.query(NavbarModel)
        if type == 'intermediate':
            results = results.filter_by(type=1)
        if visible_only:
            results = results.filter_by(is_visible=1)
        if excluded_id:
            results = results.filter(NavbarModel.id!=excluded_id)

        return results.order_by(NavbarModel.ancestor_id, NavbarModel.order).all()

    @staticmethod
    def create_navbar(form_data):
        """建立 navbar 物件

        Args:
            form_data: wtforms.forms.Form
        """
        navbar = NavbarModel()
        return DAL.sync_navbar(form_data, navbar)

    @staticmethod
    def sync_navbar(form_data, navbar):
        # 如果是內建模組，只處理幾個可以更動的設定，其他的不給變動
        if navbar.type and navbar.type in (NavbarType.BUILTIN_NEWS,
                                           NavbarType.BUILTIN_TELEXT,
                                           NavbarType.BUILTIN_LINKS):
            navbar.is_visible = 1 if form_data.is_visible.data else 0
            navbar.order = form_data.order.data
            ancestor_navbar = DAL.get_navbar(int(form_data.ancestor_id.data))
            if ancestor_navbar:
                navbar.ancestor = ancestor_navbar
            else:
                logger.error('找不到上層選單物件 %s', form_data.ancestor_id.data)
                return False
            DBSession.add(navbar)
            return True
        # 一般化的 navbar
        if form_data.type.data == NavbarType.TREE_NODE.value:
            # intermediate node
            navbar.type = NavbarType.TREE_NODE.value
            navbar.name = form_data.name.data
            if form_data.icon.data:
                navbar.icon = form_data.icon.data
            if form_data.aria_name.data:
                navbar.aria_name = form_data.aria_name.data
            else:
                logger.error('tree node 應該設定無障礙英文名稱')
                return False
        elif form_data.type.data == NavbarType.LEAF_NODE.value:
            # leaf node
            navbar.type = NavbarType.LEAF_NODE.value
            navbar.name = form_data.name.data
            if not form_data.leaf_type.data.isdigit():
                logger.error('leaf node type 值應為數值')
                return False
            if int(form_data.leaf_type.data) == NavbarLeafNodeType.PAGE:
                if form_data.page_id.data:
                    page = DAL.get_page(int(form_data.page_id.data))
                    if page:
                        navbar.page = page
                        navbar.url = None
                    else:
                        logger.error('找不到 page id 為 %s 的物件', form_data.page_id.data)
                        return False
                else:
                    logger.error('沒有指定連結的 page id')
                    return False
            elif int(form_data.leaf_type.data) == NavbarLeafNodeType.URL:
                if form_data.url.data:
                    navbar.url = form_data.url.data
                    navbar.page = None
                else:
                    logger.error('沒有指定連結的網址')
                    return False
            else:
                logger.error(f'leaf node type 為非法數值 {form_data.leaf_type.data}')
                return False
            navbar.is_href_blank = 1 if form_data.is_href_blank.data else 0
            if form_data.icon.data:
                navbar.icon = form_data.icon.data
        elif form_data.type.data == NavbarType.DROPDOWN_DIVIDER.value:
            # divider
            navbar.type = NavbarType.DROPDOWN_DIVIDER.value
            navbar.name = '分隔線'
        navbar.is_visible = 1 if form_data.is_visible.data else 0
        navbar.order = form_data.order.data
        ancestor_navbar = DAL.get_navbar(int(form_data.ancestor_id.data))
        if ancestor_navbar:
            navbar.ancestor = ancestor_navbar
        else:
            logger.error('找不到上層選單物件 %s', form_data.ancestor_id.data)
            return False
        DBSession.add(navbar)
        return True

    @staticmethod
    def get_navbar(navbar_id):
        """取得導覽列物件

        Args:
            navbar_id: NavbarModel 的 primary key

        Returns:
            回傳導覽列物件
        """
        return DBSession.get(NavbarModel, navbar_id)

    @staticmethod
    def change_navbar_ancestor_id(old_ancestor_id, new_ancestor_id):
        """將原本 ancestor_id 為 old_ancestor_id 的 records 改成新的 new_ancestor_id

        Args:
            old_ancestor_id: 作為篩選條件，找出 ancestor_id 為此值的 records
            new_ancestor_id: 將找到的 records 其 ancestor_id 改成此值

        Returns:
            None
        """
        (DBSession.query(NavbarModel)
         .filter_by(ancestor_id=old_ancestor_id)
         .update({NavbarModel.ancestor_id: new_ancestor_id}))

    @staticmethod
    def delete_navbar(navbar):
        """刪除指定的 navbar 物件

        Args:
            navbar: NavbarModel 物件
        """
        if navbar.type in (NavbarType.TREE_NODE,
                           NavbarType.LEAF_NODE,
                           NavbarType.DROPDOWN_DIVIDER):
            DBSession.delete(navbar)
            return True
        else:
            return False

    @staticmethod
    def update_site_config_list(updated_config_list):
        """更新 site config"""
        for each_config in updated_config_list:
            DBSession.query(GlobalConfigModel).filter_by(id=each_config['id']).update(each_config, synchronize_session=False)
        return True

    @staticmethod
    def get_tag_by_name(name):
        """根據傳入的標籤名稱回傳對應的標籤物件

        Args:
            name: 標籤名稱

        Returns:
            回傳標籤物件
        """
        return DBSession.query(TagModel).filter_by(name=name).one_or_none()

    @staticmethod
    def get_or_create_tag(name):
        """根據傳入的標籤名稱，回傳或建立該標籤

        Args:
            name: 標籤名稱

        Returns:
            回傳已存在或新建立的標籤
        """
        tag = DAL.get_tag_by_name(name)
        if not tag:
            tag = TagModel(name=name)
        return tag

    @staticmethod
    def get_page(page_id):
        """取得指定的單一頁面

        Args:
            page_id: 單一頁面的 primary key

        Returns:
            回傳單一頁面
        """
        return DBSession.get(PageModel, page_id)

    @staticmethod
    def create_page(form_data):
        """建立單一頁面

        Args:
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已建立的單一頁面物件
        """
        page = PageModel(title=form_data.title.data, content=form_data.content.data)
        # 處理 tags
        tags = {each_tag.strip() for each_tag in form_data.tags.data.split(',')}
        for each_tag_name in tags:
            tag = DAL.get_or_create_tag(each_tag_name)
            page.tags.append(tag)
        # 處理 groups
        group_ids = form_data.group_ids.data
        page.groups = DAL.get_groups(group_ids)
        DBSession.add(page)
        DBSession.flush()
        return page

    @staticmethod
    def update_page(page, form_data, is_admin):
        """使用 form 的資料更新指定的單一頁面

        Args:
            page: PageModel 物件
            form_data: wtforms.forms.Form 物件
            is_admin: boolean 值，用來確認執行的身份是否為管理權限，若不是，則不更動單一頁面的管理群組設定

        Returns:
            回傳已更新的單一頁面物件
        """
        page.title = form_data.title.data
        page.content = form_data.content.data
        # 處理 tag
        page.tags = []
        tags = {each_tag.strip() for each_tag in form_data.tags.data.split(',')}
        for each_tag_name in tags:
            tag = DAL.get_or_create_tag(each_tag_name)
            page.tags.append(tag)
        # 若是管理權限，則處理單一頁面的群組
        if is_admin:
            group_ids = form_data.group_ids.data
            page.groups = DAL.get_groups(group_ids)
        return page

    @staticmethod
    def delete_page(page):
        """刪除單一頁面

        Args
            page: PageModel
        """
        DBSession.delete(page)

    @staticmethod
    def get_page(page_id):
        """取得單一頁面"""
        return DBSession.get(PageModel, page_id)

    @staticmethod
    def save_page(page):
        """將單一頁面物件存入 db session 中

        Args:
            page: 單一頁面物件
        """
        DBSession.add(page)

    @staticmethod
    def create_page_attachment(original_name, real_name):
        """建立單一頁面的上傳附件選單

        Args:
            original_name: 上傳檔案的原本的名稱
            real_name: 系統產生的亂入檔名

        Returns:
            回傳該單一頁面上傳附件物件
        """
        return PageAttachmentModel(original_name=original_name, real_name=real_name)

    @staticmethod
    def delete_page_attachment(page_attachment):
        """刪除指定的 PageAttachment

        Args:
            page_attachment: PageAttachment 物件
        """
        DBSession.delete(page_attachment)

    @staticmethod
    def get_page_quantity_of_total_pages(quantity_per_page, group_id=None):
        """回傳單一頁面列表總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆單一頁面
            group_id: 若有指定，則只會傳回符合此群組的單一頁面頁數

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(PageModel.id))
        if group_id:
            results = results.filter(GroupModel.id==group_id)
        return math.ceil(results.scalar()/quantity_per_page)

    @staticmethod
    def get_page_list(page_number=1, quantity_per_page=20, group_id=None, pagination=True):
        """傳回單一頁面列表

        Args:
            page_number: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            group_id: 指定要撈取的使用者群組，None 代表不指定
            pagination: 代表是否要分頁，預設為要分頁，若為 False 代表不分頁傳回全部的單一頁面

        Returns:
            回傳單一頁面列表
        """
        results = DBSession.query(PageModel)
        if group_id:
            results = results.filter(GroupModel.id == group_id)
        if pagination:
            return (results.order_by(PageModel.id.desc())
                        [(page_number-1)*quantity_per_page : (page_number-1)*quantity_per_page+quantity_per_page])
        else:
            return results.all()

    @staticmethod
    def get_news_category(category_id):
        """取得指定的 news category 物件

        Args:
            category_id: news category 的 id

        Returns:
            回傳 NewsCategory 物件
        """
        return DBSession.query(NewsCategoryModel).filter_by(id=category_id).one_or_none()

    @staticmethod
    def get_news_qty():
        """取得最新消息總數並回傳

        Returns:
            回傳最新消息總數
        """
        return DBSession.query(func.count(NewsModel.id)).scalar()

    @staticmethod
    def create_news(form_data):
        """建立最新消息

        Args:
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已建立的最新消息物件
        """
        news = NewsModel(title=form_data.title.data,
                         content=form_data.content.data,
                         group_id=form_data.group_id.data,
                         category_id=form_data.category_id.data)

        # 處理置頂的邏輯，如果勾選了置頂，就順便紀錄置頂的起訖時間
        if form_data.is_pinned.data:
            news.pinned_start_datetime = form_data.pinned_start_datetime.data
            news.pinned_end_datetime = form_data.pinned_end_datetime.data
            news.is_pinned = PinnedType.IS_PINNED.value

        news.visible_start_datetime = form_data.visible_start_datetime.data
        news.visible_end_datetime = form_data.visible_end_datetime.data

        if news.visible_start_datetime:
            news.viewable_datetime = news.visible_start_datetime

        # 處理 tags
        tags = {each_tag.strip() for each_tag in form_data.tags.data.split(',')}
        for each_tag_name in tags:
            tag = DAL.get_or_create_tag(each_tag_name)
            news.tags.append(tag)

        DBSession.add(news)
        DBSession.flush()

        return news

    @staticmethod
    def create_news_attachment(original_name, real_name):
        """建立最新消息的上傳附件選單

        Args:
            original_name: 上傳檔案的原本的名稱
            real_name: 系統產生的亂入檔名

        Returns:
            回傳該單一頁面上傳附件物件
        """
        return NewsAttachmentModel(original_name=original_name, real_name=real_name)

    @staticmethod
    def save_news(news):
        """將最新消息物件存入 db session 中

        Args:
            page: 最新消息物件
        """
        if news.visible_start_datetime:
            news.viewable_datetime = news.visible_start_datetime
        DBSession.add(news)

    @staticmethod
    def get_news(news_id):
        """取得 NewsModel 物件

        Args:
            news_id: news 的 primary key

        Returns:
            回傳 NewsModel
        """
        return DBSession.get(NewsModel, news_id)

    @staticmethod
    def get_frontend_news(news_id):
        """取得前台有存取權限的最新消息，會檢查是否超過顯示時間

        Args:
             news_id: news 的 primary key

        Returns:
            回傳 NewsModel，若找不到或已無法顯示回傳 None
        """
        news = DAL.get_news(news_id)
        if news:
            now = datetime.now()
            if news.visible_start_datetime:
                if not news.visible_start_datetime <= now:
                    return None
            if news.visible_end_datetime:
                if not now < news.visible_end_datetime:
                    return None
            return news

    @staticmethod
    def delete_news(news):
        """刪除最新消息

        Args:
            news: NewsModel
        """
        DBSession.delete(news)

    @staticmethod
    def update_news(news, form_data):
        """使用 form 的資料更新指定的最新消息

        Args:
            news: NewsModel 物件
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已更新的最新消息物件
        """
        news.title = form_data.title.data
        news.content = form_data.content.data
        news.group_id = form_data.group_id.data
        news.category_id = form_data.category_id.data

        # 處理置頂的邏輯，如果勾選了置頂，就順便紀錄置頂的起訖時間
        if form_data.is_pinned.data:
            news.pinned_start_datetime = form_data.pinned_start_datetime.data
            news.pinned_end_datetime = form_data.pinned_end_datetime.data
            news.is_pinned = PinnedType.IS_PINNED.value

        news.visible_start_datetime = form_data.visible_start_datetime.data
        news.visible_end_datetime = form_data.visible_end_datetime.data

        if news.visible_start_datetime:
            news.viewable_datetime = news.visible_start_datetime

        # 處理 tags
        tags = {each_tag.strip() for each_tag in form_data.tags.data.split(',')}
        for each_tag_name in tags:
            tag = DAL.get_or_create_tag(each_tag_name)
            news.tags.append(tag)

        DBSession.add(news)

        return news

    @staticmethod
    def delete_news_attachment(news_attachment):
        """刪除指定的 NewsAttachment

        Args:
            news_attachment: NewsAttachment 物件
        """
        DBSession.delete(news_attachment)

    @staticmethod
    def create_news_category(form_data):
        """建立最新消息的分類

        Args:
            form_data: wtforms.forms.Form

        Returns:
            回傳建立的 news category
        """
        news_category = NewsCategoryModel()
        form_data.populate_obj(news_category)
        DBSession.add(news_category)

    @staticmethod
    def get_page_quantity_of_total_news_categories(quantity_per_page):
        """回傳最新消息分頁總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息分類

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(NewsCategoryModel.id))
        return math.ceil(results.scalar() / quantity_per_page)

    @staticmethod
    def delete_news_category(news_category_id):
        """刪除指定的最新消息分類

        Args:
            news_category_id: 最新消息分類的 primary key

        Returns:
            若回傳 False 代表該分類還有相依的最新消息
        """
        try:
            DBSession.query(NewsCategoryModel).filter_by(id=news_category_id).delete()
            return True
        except IntegrityError:
            return False

    @staticmethod
    def update_news_category(news_category, form_data):
        """使用 form 的資料更新指定的最新消息

        Args:
            news_category: NewsCategoryModel 物件
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已更新的最新消息分類物件
        """
        form_data.populate_obj(news_category)
        DBSession.add(news_category)

    @staticmethod
    def get_link(link_id):
        """取得 LinkModel 物件

        Args:
            link_id: LinkModel 的 primary key

        Returns:
            回傳 LinkModel 物件
        """
        return DBSession.get(LinkModel, link_id)

    @staticmethod
    def get_links_qty():
        """取得好站連結總數並回傳

        Returns:
            回傳好站連結總數
        """
        return DBSession.query(func.count(LinkModel.id)).scalar()

    @staticmethod
    def get_link_category_list():
        """回傳好站連結分類列表"""
        return DBSession.query(LinkCategoryModel).order_by(LinkCategoryModel.order)

    @staticmethod
    def create_link(form_data):
        """建立好站連結

        Args:
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已建立的好站連結物件
        """
        link = LinkModel(title=form_data.title.data,
                         url=form_data.url.data,
                         icon='',
                         group_id=form_data.group_id.data,
                         category_id=form_data.category_id.data)

        link.is_pinned = PinnedType.IS_PINNED.value if form_data.is_pinned.data else PinnedType.IS_NOT_PINNED.value
        DBSession.add(link)
        DBSession.flush()
        return link

    @staticmethod
    def save_link(link):
        """儲存 link model

        Args:
            link: LinkModel 物件
        """
        DBSession.add(link)

    @staticmethod
    def get_link_list(page_number=1, quantity_per_page=20, category_id=None):
        """傳回好站連結列表

        Args:
            page_number: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            category_id: 指定要撈取的好站連結分類，None 代表不指定

        Returns:
            回傳好站連結列表
        """
        results = DBSession.query(LinkModel)
        if category_id:
            results = results.filter_by(category_id=category_id)
        return (results.order_by(LinkModel.is_pinned.desc(), LinkModel.id.desc())
                    [(page_number - 1) * quantity_per_page: (page_number - 1) * quantity_per_page + quantity_per_page])

    @staticmethod
    def get_pinned_link_list():
        """取得需要顯示在首頁上的好站連結"""
        return DBSession.query(LinkModel).filter_by(is_pinned=PinnedType.IS_PINNED.value)

    @staticmethod
    def get_page_quantity_of_total_link(quantity_per_page, category_id=None):
        """回傳好站連結總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息
            category_id: 若有指定，則只會傳回符合此分類的好站連結頁數

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(LinkModel.id))
        if category_id:
            results = results.filter_by(category_id=category_id)
        return math.ceil(results.scalar() / quantity_per_page)

    @staticmethod
    def delete_link(link):
        """刪除好站連結

        Args:
            link: LinkModel
        """
        DBSession.delete(link)

    @staticmethod
    def update_link(link, form_data):
        """使用 form 的資料更新指定的好站連結

        Args:
            link: LinkModel 物件
            form_data: wtforms.forms.Form 物件
        """
        link.title = form_data.title.data
        link.url = form_data.url.data
        link.is_pinned = PinnedType.IS_PINNED.value if form_data.is_pinned.data else PinnedType.IS_NOT_PINNED.value
        return link

    @staticmethod
    def save_link(link):
        """將好站連結物件存入 db session 中

        Args:
            link: 好站連結物件
        """
        DBSession.add(link)

    @staticmethod
    def create_link_category(form_data):
        """建立好站連結的分類

        Args:
            form_data: wtforms.forms.Form

        Returns:
            回傳建立的 link category
        """
        link_category = LinkCategoryModel()
        form_data.populate_obj(link_category)
        DBSession.add(link_category)

    @staticmethod
    def get_page_quantity_of_total_link_categories(quantity_per_page):
        """回傳好站連結分頁總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆好站連結分類

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(LinkCategoryModel.id))
        return math.ceil(results.scalar() / quantity_per_page)

    @staticmethod
    def delete_link_category(link_category_id):
        """刪除指定的好站連結分類

        Args:
            link_category_id: 好站連結分類的 primary key

        Returns:
            若回傳 False 代表該分類還有相依的好站連結
        """
        try:
            DBSession.query(LinkCategoryModel).filter_by(id=link_category_id).delete()
            return True
        except IntegrityError:
            return False

    @staticmethod
    def get_link_category_list():
        """回傳好站連結分類列表"""
        return DBSession.query(LinkCategoryModel).order_by(LinkCategoryModel.order)

    @staticmethod
    def update_link_category(link_category, form_data):
        """使用 form 的資料更新指定的好站連結

        Args:
            link_category: LinkCategoryModel 物件
            form_data: wtforms.forms.Form 物件

        Returns:
            回傳已更新的好站連結分類物件
        """
        form_data.populate_obj(link_category)
        DBSession.add(link_category)

    @staticmethod
    def get_link_category(category_id):
        """取得指定的 link category 物件

        Args:
            category_id: link category 的 id

        Returns:
            回傳 LinkCategory 物件
        """
        return DBSession.get(LinkCategoryModel, category_id)

    @staticmethod
    def get_page_quantity_of_total_links(quantity_per_page, category_id=None):
        """回傳好站連結總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆好站連結
            category_id: 若有指定，則只會傳回符合此分類的好站連結頁數

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(LinkModel.id))
        if category_id:
            results = results.filter_by(category_id=category_id)
        return math.ceil(results.scalar() / quantity_per_page)

    @staticmethod
    def create_telext(form_data):
        """建立分機表

        Args:
            form_data: wtforms.forms.Form
        """
        telext = TelExtModel()
        form_data.populate_obj(telext)
        telext.is_pinned = PinnedType.IS_PINNED.value if form_data.is_pinned.data else PinnedType.IS_NOT_PINNED.value
        DBSession.add(telext)

    @staticmethod
    def get_telext_list():
        """回傳分機表列表"""
        return DBSession.query(TelExtModel).order_by(TelExtModel.order)

    @staticmethod
    def get_telext_qty():
        """取得分機表總數並回傳

        Returns:
            回傳分機表總數
        """
        return DBSession.query(func.count(TelExtModel.id)).scalar()

    @staticmethod
    def get_pinned_telext_list():
        """回傳根據 order 排序指定顯示在首頁的分機表"""
        return (DBSession.query(TelExtModel)
                .filter_by(is_pinned=PinnedType.IS_PINNED.value)
                .order_by(TelExtModel.order))

    @staticmethod
    def delete_telext(telext_id):
        """刪除分機

        Args:
            telext_id: TelExtModel 的 primary key
        """
        DBSession.query(TelExtModel).filter_by(id=telext_id).delete()

    @staticmethod
    def update_telext(telext_id, form_data):
        """更新分機表

        Args:
            telext_id: 分機表 TelExtModel 的 primary key
            form_data: wtforms.forms.Form
        """
        telext = DBSession.get(TelExtModel, telext_id)
        if telext:
            form_data.populate_obj(telext)
            telext.is_pinned = PinnedType.IS_PINNED.value if form_data.is_pinned.data else PinnedType.IS_NOT_PINNED.value
            DBSession.add(telext)
            return True
        return False

    @staticmethod
    def get_telext(telext_id):
        """取得分機

        Args:
            telext_id: 分機表 TelExtModel 的 primary key
        """
        return DBSession.get(TelExtModel, telext_id)

    @staticmethod
    def log_auth(auth_log_type, user_id, client_addr, source):
        """紀錄使用者的認証

        Args:
            auth_log_type: enum.AuthLogType
            user_id: 使用者的 id
            client_addr: 來源端的 ip 位址
            source: 認証管道來源
        """
        auth_log = AuthLogModel(type=int(auth_log_type), user_id=user_id, client_addr=client_addr, source=source)
        DBSession.add(auth_log)

    @staticmethod
    def get_auth_log_list(page_number=1, quantity_per_page=20, user_id=None):
        """傳回 auth log 紀錄列表

        Args:
            page_number: 指定頁數，若沒指定則回傳第一頁
            quantity_per_page: 指定每頁的筆數，預設為 20 筆
            user_id: 指定要撈取的使用者 auth log，None 代表全部撈出

        Returns:
            回傳 auth log 列表
        """
        results = DBSession.query(AuthLogModel)
        if user_id:
            results = results.filter_by(user_id=user_id)
        return (results.order_by(AuthLogModel.id.desc())
                   [(page_number-1)*quantity_per_page : (page_number-1)*quantity_per_page+quantity_per_page])

    @staticmethod
    def get_today_successful_auth_qty():
        """傳回本日登入成功的數量

        Returns:
            回傳本日登入成功的數量
        """
        return (DBSession.query(func.count(AuthLogModel.id))
                         .filter(AuthLogModel.datetime+timedelta(days=1)>datetime.now(),
                                 AuthLogModel.type==AuthLogType.LOGIN.value)
                         .scalar())

    @staticmethod
    def get_today_wrong_password_auth_qty():
        """傳回本日登入密碼錯誤的數量

        Returns:
            回傳本日登入密碼錯誤的數量
        """
        return (DBSession.query(func.count(AuthLogModel.id))
                .filter(AuthLogModel.datetime+timedelta(days=1)>datetime.now(),
                        AuthLogModel.type==AuthLogType.WRONG_PASSWORD.value)
                .scalar())

    @staticmethod
    def get_page_quantity_of_total_auth_logs(quantity_per_page, user_id=None):
        """回傳 auth logs 總共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息
            user_id: 若有指定，則只會根據指定 user id 的 auth logs 去計算頁數

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(AuthLogModel.id))
        if user_id:
            results = results.filter_by(user_id=user_id)
        return math.ceil(results.scalar()/quantity_per_page)

    @staticmethod
    def get_api_token_list():
        """回傳 api token 列表

        Returns:
            APIToken model 的列表
        """
        return DBSession.query(APITokenModel)

    @staticmethod
    def create_api_token():
        """產生一個 APITokenModel 並回傳

        Returns:
            APITokenModel
        """
        return APITokenModel()

    @staticmethod
    def save_api_token(api_token, value=None):
        """儲存 api token

        Args:
            api_token: APITokenModel 實體

        Returns:
            成功回傳 True
        """
        if value is None:
            available_characters = string.ascii_letters + string.digits
            key_length = 32
            token = 'token-' + ''.join(random.choice(available_characters) for i in range(key_length))
            api_token.value = token
        else:
            api_token.value = value
        DBSession.add(api_token)
        return True

    @staticmethod
    def get_api_token(token):
        return DBSession.query(APITokenModel).filter_by(value=token).one_or_none()

    @staticmethod
    def get_page_quantity_of_total_search_results(quantity_per_page, key, value):
        """回傳搜尋結果共有幾頁

        Args:
            quantity_per_page: 每頁幾筆最新消息
            key: 搜尋的欄位
            value: 搜尋的內容

        Returns:
            回傳總共頁數
        """
        results = DBSession.query(func.count(NewsModel.id))
        if key == 'publisher':
            results = results.join(GroupModel).filter(GroupModel.name.like(f'%{value}%'))
        elif key == 'title':
            results = results.filter(NewsModel.title.like(f'%{value}%'))
        else:
            results = results.filter(NewsModel.content.like(f'%{value}%'))
        return math.ceil(results.scalar()/quantity_per_page)

    @staticmethod
    def get_search_results(key, value, quantity_per_page, page_number):
        if key == 'publisher':
            results = DBSession.query(NewsModel).join(GroupModel).filter(GroupModel.name.like(f'%{value}%')).order_by(NewsModel.id.desc())
        elif key == 'title':
            results = DBSession.query(NewsModel).filter(NewsModel.title.like(f'%{value}%')).order_by(NewsModel.id.desc())
        else:
            results = DBSession.query(NewsModel).filter(NewsModel.content.like(f'%{value}%')).order_by(NewsModel.id.desc())
        return results.limit(quantity_per_page).offset((page_number-1)*quantity_per_page)

