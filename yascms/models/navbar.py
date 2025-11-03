from sqlalchemy import (Column,
                        Integer,
                        String,
                        Text,
                        ForeignKey)
from sqlalchemy.schema import Identity
from sqlalchemy.orm import relationship
from pyramid_sqlalchemy import BaseObject

from yascms.models.page import PageModel


class NavbarModel(BaseObject):
    """定義導覽列，其為巢狀架構"""

    __tablename__ = 'navbar'

    # 各導覽列元素的 id，若為 builtin 模組，則統一為 -1 以方便辨識（因為不會存入 db 所以不會有 primary key duplicated 的問題
    id = Column(Integer, Identity(always=True), primary_key=True)

    # 選單名稱
    name = Column(String(50), nullable=False, server_default='')

    # 無障礙導覽列英文名稱，若是 intermediate node 就要設定； leaf node 就不用
    aria_name = Column(String(50), nullable=True)

    # 連結的 url，若這個 navbar 是連結了單一頁面，則 url 就會是 null，跟下面的 page_id 互斥
    url = Column(Text, nullable=True)

    # 連結的單一頁面，若是連結 url 則 page_id 就會是 null，跟上面的 url 互斥
    page_id = Column(Integer, ForeignKey('pages.id'))
    page = relationship(PageModel, back_populates='navbar')

    # 是否另開分頁，若是，點選連結時另開分頁
    is_href_blank = Column(Integer, nullable=False, default=0, server_default='0')

    # 使用的 fontawesome icon
    icon = Column(String(50), nullable=False, default='', server_default='')

    # 選單類型，請參見 yascms.enum.NavbarType 的註解
    type = Column(Integer, nullable=False)

    # 內建的模組才會用到此欄位，用來讓程式判斷這是哪一個模組，以調用該模組的選單產生
    module_name = Column(String(50), nullable=True)

    # 排序
    order = Column(Integer, nullable=False, default=0, server_default='0')

    # 是否顯示，有時候只是想暫時隱藏。 0 代表隱藏， 1 代表顯示
    is_visible = Column(Integer, nullable=False, default=1, server_default='1')

    # self-referential relationship
    ancestor_id  = Column(Integer, ForeignKey('navbar.id'))
    ancestor = relationship('NavbarModel', backref='descendants', remote_side=[id])
