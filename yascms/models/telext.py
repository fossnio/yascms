from datetime import datetime

from sqlalchemy import (Column,
                        Integer,
                        String,
                        DateTime)
from sqlalchemy.schema import Identity
from pyramid_sqlalchemy import BaseObject


class TelExtModel(BaseObject):
    """分機表"""

    __tablename__ = 'telext'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # 標題
    title = Column(String(50), nullable=False, index=True)

    # 分機號碼
    ext = Column(String(50), nullable=False)

    # 排序
    order = Column(Integer, nullable=False, default=0, server_default='0')

    # 是否顯示在釘選在首頁
    is_pinned = Column(Integer, nullable=False, default=0, server_default='0')

    # 發佈時間，建立這篇好站連結當下的時間
    publication_datetime = Column(DateTime, nullable=False, default=datetime.now)

    # 最後更新時間
    last_updated_datetime = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
