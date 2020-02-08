from sqlalchemy import (Column,
                        Integer,
                        String,
                        ForeignKey)
from sqlalchemy.orm import relationship

from pyramid_sqlalchemy import BaseObject


class NavbarModel(BaseObject):
    """用來定義主選單，其為巢狀架構"""

    __tablename__ = 'navbar'

    id = Column(Integer, primary_key=True)

    # 選單名稱
    name = Column(String(50), nullable=False, server_default='')

    # 連結的 url
    link = Column(String(190), nullable=False, default='', server_default='')

    # 排序
    order = Column(Integer, nullable=False, default=0, server_default='0')

    # self-referential relationship
    ancestor_id  = Column(Integer, ForeignKey('navbar.id'))
    ancestor = relationship('NavbarModel', backref='descendants', remote_side=[id])