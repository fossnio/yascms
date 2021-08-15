import json
import shutil

import transaction

from tp_yass.dal import DAL
from tp_yass.helpers import get_project_abspath


class ThemeImporter:
    """用來處理匯入樣板"""

    def __init__(self, theme_name, base_dir=None):
        """初始化

        Args:
            theme_name: 樣板名稱
            base_dir: 作為 root dir 的起點，為 pathlib.PosixPath 的實體。若沒有指定則會使用 tp_yass 專案的 base dir
        """
        self.theme_name = theme_name
        if base_dir is None:
            self.base_dir = get_project_abspath()
        else:
            self.base_dir = base_dir
        self.default_dest = self.base_dir / 'uploads/themes' / self.theme_name / 'banners'

    def import_theme(self):
        self._import_theme_config()
        self.import_theme_banners()

    def import_theme_banners(self, src=None, dest=None):
        """匯入指定的佈景主題橫幅檔案"""
        if src is None:
            src = self.base_dir / 'themes' / self.theme_name / 'static/img/banners'
        if dest is None:
            dest = self.default_dest
        dest.mkdir(parents=True, exist_ok=True)
        for banner in src.glob('*'):
            shutil.copy(banner, dest)

    def _import_theme_config(self):
        """匯入指定的佈景主題設定檔"""
        with transaction.manager, open(self.base_dir / 'themes' / self.theme_name / 'config.json') as f:
            config = json.loads(f.read())
            DAL.add_theme_config(config)
