import os
import json
import pathlib
import zipfile
import logging
import shutil
from tempfile import NamedTemporaryFile, TemporaryDirectory

from pyramid.view import view_config, view_defaults
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound

from yascms.dal import DAL
from yascms.enum import ThemeConfigCustomType, HomepageItemType, HomepageItemParamsSubType
from yascms.helpers import get_project_abspath
from yascms.helpers.file import save_file
from yascms.helpers.backend.theme_config import ThemeController
from yascms.forms.backend.theme_config import (ThemeConfigGeneralForm,
                                                ThemeConfigBannersEditForm,
                                                ThemeConfigBannersUploadForm,
                                                ThemeConfigUploadForm, ThemeConfigHomepageItemsOrderEditForm)


logger = logging.getLogger(__name__)


@view_config(route_name='backend_theme_config_list',
             renderer='',
             permission='view')
def theme_config_list_view(request):
    request.override_renderer = f'yascms:themes/{request.effective_theme_name}/backend/theme_config_list.jinja2'
    return {'theme_config_list': DAL.get_theme_config_list()}


@view_config(route_name='backend_theme_config_activate', permission='edit')
def theme_config_activate_view(request):
    """將預設的樣板設定成指定的樣板"""
    theme_name = request.matchdict['theme_name']
    if theme_name in request.cache.get_available_theme_name_list():
        DAL.set_current_theme_name(theme_name)
        request.cache.delete_current_theme_name()
        request.cache.delete_current_theme_config()
    return HTTPFound(location=request.route_url('backend_theme_config_list'))


@view_config(route_name='backend_theme_config_delete', permission='edit')
def theme_config_delete_view(request):
    """刪除指定的樣板"""
    theme_name = request.matchdict['theme_name']
    if (theme_name in request.cache.get_available_theme_name_list() and
        theme_name != request.current_theme_name):

        ThemeController(theme_name).delete_theme()
    return HTTPFound(location=request.route_url('backend_theme_config_list'))


@view_defaults(route_name='backend_theme_config_upload',
               renderer='',
               permission='edit')
class ThemeConfigUploadView:
    """用來處理樣板的上傳"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/theme_config_upload.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        form = ThemeConfigUploadForm()
        return {'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        form = ThemeConfigUploadForm(self.request.POST)
        if form.validate():
            with TemporaryDirectory() as tmpdirname:
                dest_file_name = f'{tmpdirname}/{form.theme.data.filename}'
                with open(dest_file_name, 'wb') as dest_file:
                    save_file(form.theme.data, dest_file)
                try:
                    with zipfile.ZipFile(dest_file_name, 'r') as zip_fp:
                        zip_fp.extractall(tmpdirname)
                except zipfile.BadZipFile:
                    self.request.session.flash('解壓縮失敗，請確認檔案格式為合格的 zip 壓縮格式', 'fail')
                    return {'form': form}
                pathlib.PosixPath(dest_file_name).unlink()
                for each_theme in pathlib.PosixPath(tmpdirname).glob('*'):
                    dest_theme_dir = get_project_abspath() / 'themes' / each_theme.name
                    if form.is_overwrite.data and dest_theme_dir.exists():
                        shutil.rmtree(dest_theme_dir.as_posix())
                        ThemeController(each_theme.name).delete_theme()
                    else:
                        if dest_theme_dir.exists():
                            self.request.session.flash(f'樣板 {each_theme.name} 目錄已存在，請先刪除或上傳時勾選覆寫樣板', 'fail')
                            continue
                    shutil.move(each_theme.as_posix(), dest_theme_dir.as_posix())
                    ThemeController(each_theme.name).import_theme()
                    self.request.session.flash(f'匯入樣板 {each_theme.name} 成功', 'success')
            self.request.cache.delete_available_theme_name_list()
            return HTTPFound(location=self.request.route_url('backend_theme_config_list'))
        else:
            return {'form': form}


@view_defaults(route_name='backend_theme_config_general_edit',
               renderer='',
               permission='edit')
class ThemeConfigGeneralEditView:
    """處理樣板的設定值內容"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/theme_config_general_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigGeneralForm()
        form.custom_css.default = theme_config['settings']['custom_css']['value']
        form.custom_css_visible.default = theme_config['settings']['custom_css']['visible']
        form.custom_js.default = theme_config['settings']['custom_js']['value']
        form.custom_js_visible.default = theme_config['settings']['custom_js']['visible']
        form.process()
        for each_custom_setting in theme_config['settings']['custom']['value']:
            form.custom.append_entry(each_custom_setting)
        return {'theme_config': theme_config,
                'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigGeneralForm(self.request.POST)
        if form.validate():
            theme_config['settings']['custom_css']['value'] = form.custom_css.data
            theme_config['settings']['custom_css']['visible'] = form.custom_css_visible.data
            theme_config['settings']['custom_js']['value'] = form.custom_js.data
            theme_config['settings']['custom_js']['visible'] = form.custom_js_visible.data
            custom_value = form.custom.data
            try:
                for each_setting in custom_value:
                    if each_setting['type'] == ThemeConfigCustomType.BOOLEAN:
                        if each_setting['value'].upper() in ('FALSE', '0', ''):
                            each_setting['value'] = False
                        else:
                            each_setting['value'] = True
                    elif each_setting['type'] == ThemeConfigCustomType.INTEGER:
                        each_setting['value'] = int(each_setting['value'])
                theme_config['settings']['custom']['value'] = custom_value
            except ValueError as e:
                pass
            DAL.update_theme_config(theme_config)
            self.request.cache.delete_current_theme_config()
            return HTTPFound(location=self.request.route_url('backend_theme_config_list'))
        return {'theme_config': theme_config,
                'form': form}


@view_defaults(route_name='backend_theme_config_banners_edit',
               renderer='',
               permission='edit')
class ThemeConfigBannersEditView:
    """用來處理橫幅的列表與增刪"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/theme_config_banners_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigBannersEditForm()
        banners_dict = self._get_banners(theme_name)
        for each_banner in banners_dict:
            if each_banner in theme_config['settings']['banners']['value']:
                each_banner_is_visible = True
            else:
                each_banner_is_visible = False
            form.banners.append_entry({'name': each_banner, 'is_visible': each_banner_is_visible})
        return {'theme_config': theme_config, 'form': form, 'banners_dict': banners_dict}

    @view_config(request_method='POST')
    def post_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigBannersEditForm(self.request.POST)
        banners_dict = self._get_banners(theme_name)
        if form.validate():
            theme_config_changed = False
            for each_banner in form.banners:
                if each_banner.data['name'] in banners_dict:
                    if each_banner.data['is_visible'] and (each_banner.data['name'] not in theme_config['settings']['banners']['value']):
                        theme_config['settings']['banners']['value'].append(each_banner.data['name'])
                        theme_config_changed = True
                    elif (not each_banner.data['is_visible']) and (each_banner.data['name'] in theme_config['settings']['banners']['value']):
                        theme_config['settings']['banners']['value'].remove(each_banner.data['name'])
                        theme_config_changed = True
            if theme_config_changed:
                DAL.update_theme_config(theme_config)
                self.request.cache.delete_current_theme_config()
            return HTTPFound(location=self.request.route_url('backend_theme_config_list'))
        else:
            return {'theme_config': theme_config, 'form': form, 'banners_dict': banners_dict}

    def _get_banners(self, theme_name):
        """回傳一個由 banner 檔名與 url 組成的 dict"""
        banners = {}
        for each_banner in sorted((get_project_abspath() / 'uploads/themes' / theme_name / 'banners').glob('*')):
            if each_banner.name.startswith('.'):
                continue
            banners[each_banner.name] = \
                self.request.static_url(f'yascms:uploads/themes/{theme_name}/banners/{each_banner.name}')
        return banners


@view_defaults(route_name='backend_theme_config_banners_upload',
               renderer='',
               permission='edit')
class ThemeConfigBannersUploadView:
    """用來處理橫幅的上傳"""

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/theme_config_banners_upload.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigBannersUploadForm()
        return {'theme_config': theme_config, 'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigBannersUploadForm(self.request.POST)
        if form.validate():
            theme_importer = ThemeController(theme_name)
            for each_file in form.banners.data:
                dest_file = NamedTemporaryFile(prefix='banner',
                                               suffix=f'.{each_file.filename.split(".")[1]}',
                                               delete=False,
                                               dir=theme_importer.uploaded_banners_dir)
                save_file(each_file, dest_file)
                dest_file.flush()
            return HTTPFound(location=self.request.route_url('backend_theme_config_banners_edit', theme_name=theme_name))
        else:
            return {'theme_config': theme_config, 'form': form}


@view_config(route_name='backend_theme_config_banners_delete', permission='edit')
def theme_config_banners_delete_view(request):
    theme_name = request.matchdict['theme_name']
    banner_name = request.matchdict['banner_name']
    theme_config = DAL.get_theme_config(theme_name)
    theme_config_changed = False

    banner_full_path = get_project_abspath() / f'uploads/themes/{theme_name}/banners/{banner_name}'
    if banner_full_path.exists():
        banner_full_path.unlink()
        if banner_full_path.name in theme_config['settings']['banners']['value']:
            theme_config['settings']['banners']['value'].remove(banner_full_path.name)
            theme_config_changed = True
    if theme_config_changed:
        DAL.update_theme_config(theme_config)
        request.cache.delete_current_theme_config()
    return HTTPFound(location=request.route_url('backend_theme_config_banners_edit', theme_name=theme_name))


@view_defaults(route_name='backend_theme_config_homepage_items_order_edit', renderer='', permission='edit')
class ThemeConfigHomepageItemsOrderEditView:

    def __init__(self, request):
        self.request = request
        self.request.override_renderer = f'yascms:themes/{self.request.effective_theme_name}/backend/theme_config_homepage_items_order_edit.jinja2'

    @view_config(request_method='GET')
    def get_view(self):
        theme_config = DAL.get_theme_config(self.request.matchdict['theme_name'])
        form = ThemeConfigHomepageItemsOrderEditForm(config=json.dumps(theme_config['settings']['homepage_items_order']['value'], ensure_ascii=False))
        return {'theme_config': theme_config,
                'news_category_list': DAL.get_news_category_list(),
                'page_list': DAL.get_page_list(pagination=False),
                'link_category_list': DAL.get_link_category_list(),
                'HomepageItemType': HomepageItemType,
                'HomepageItemParamsSubType': HomepageItemParamsSubType,
                'form': form}

    @view_config(request_method='POST')
    def post_view(self):
        theme_name = self.request.matchdict['theme_name']
        theme_config = DAL.get_theme_config(theme_name)
        form = ThemeConfigHomepageItemsOrderEditForm(self.request.POST)
        if form.validate():
            theme_config['settings']['homepage_items_order']['value'] = json.loads(form.config.data)
            DAL.update_theme_config(theme_config)
            if theme_name == self.request.cache.get_current_theme_name():
                self.request.cache.delete_current_theme_config()
            msg = f'樣板 {theme_name} 的首頁物件順序更新成功'
            logger.info(msg)
            self.request.session.flash(msg, 'success')
            return HTTPFound(location=self.request.route_url('backend_theme_config_list'))
        else:
            return {'theme_config': theme_config,
                    'news_category_list': DAL.get_news_category_list(),
                    'page_list': DAL.get_page_list(pagination=False),
                    'link_category_list': DAL.get_link_category_list(),
                    'HomepageItemType': HomepageItemType,
                    'HomepageItemParamsSubType': HomepageItemParamsSubType,
                    'form': form}


@view_config(route_name='backend_theme_config_download')
def backend_theme_config_download_view(request):
    """下載樣板"""
    theme_name = request.matchdict['theme_name']
    src_theme_dir = get_project_abspath() / 'themes'
    temp_zip_file = NamedTemporaryFile()
    shutil.make_archive(temp_zip_file.name, 'zip', root_dir=src_theme_dir.as_posix(), base_dir=theme_name)
    response = Response(body=open(f'{temp_zip_file.name}.zip', 'rb').read())
    response.headers['Content-Disposition'] = f'attachment;filename={theme_name}.zip'
    temp_zip_file.close()
    os.unlink(f'{temp_zip_file.name}.zip')
    return response
