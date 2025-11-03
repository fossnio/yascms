from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.schema import Identity
from pyramid_sqlalchemy import BaseObject


class ThemeConfigModel(BaseObject):
    '''存放佈景主題的設定值'''

    __tablename__ = 'theme_config'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # 設定名稱
    name= Column(String(50), nullable=False, unique=True)

    # 設定值
    value = Column(Text, nullable=False)
