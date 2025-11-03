from datetime import datetime

from pyramid_sqlalchemy import BaseObject
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.schema import Identity


class AuthLogModel(BaseObject):
    """帳號事件，用來紀錄像是登入登出、更改密碼等紀錄"""

    __tablename__ = 'auth_logs'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # log 紀錄的時間
    datetime = Column(DateTime, nullable=False, default=datetime.now)

    # client address，可能是 ipv4 或 ipv6 所以長度要夠
    client_addr = Column(String(48), nullable=False)

    # 類型，請參照 yascms.enum.AuthLogType 定義
    type = Column(Integer, nullable=False)

    # 來源，可以用來紀錄是透過何種管道登入登出系統
    source = Column(String(20), nullable=False)

    # 此 log 事件關聯到的帳號
    user_id = Column(Integer, ForeignKey('users.id'))
