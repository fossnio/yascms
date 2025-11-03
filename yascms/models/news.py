from datetime import datetime

from sqlalchemy import (Column,
                        Integer,
                        String,
                        DateTime,
                        Date,
                        ForeignKey)
from sqlalchemy.schema import Identity
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from pyramid_sqlalchemy import BaseObject

from yascms.models.association import news_tags_association


class NewsAttachmentModel(BaseObject):
    """news 的上傳附檔"""

    __tablename__ = 'news_attachments'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # 上傳時原本的檔案名稱
    original_name = Column(String(100), nullable=False)

    # 儲存至硬碟上的檔案名稱
    real_name = Column(String(100), nullable=False)

    news_id = Column(Integer, ForeignKey('news.id'))


class NewsModel(BaseObject):

    __tablename__ = 'news'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # 標題
    title = Column(String(100), nullable=False, index=True)

    # 內容
    content = Column(LONGTEXT, nullable=False, default='')

    # 上傳附件
    attachments = relationship('NewsAttachmentModel', backref='news', cascade='all, delete-orphan')

    # 是否置頂
    is_pinned = Column(Integer, nullable=False, default=0, server_default='0')

    # 置頂開始時間
    pinned_start_datetime = Column(Date)

    # 置頂結束時間
    pinned_end_datetime = Column(Date)

    # 是否讓這篇最新消息顯示。若為 False 則不會顯示在前台，不管下面的其他設定。
    is_visible = Column(Integer, nullable=False, default=1, server_default='1')

    # 內容是否為 html ，因為要往無障礙的方向去修正，未來新的最新消息只能貼純文字，
    # 等到全部的最新消息都是純文字後此欄位可移除
    is_html = Column(Integer, nullable=False, default=0, server_default='0')

    # 顯示開始時間，時間到了才會顯示在網頁上。若沒指定（null）則代表馬上顯示
    visible_start_datetime = Column(DateTime)

    # 顯示結束時間，時間到了才會消失在網頁上。若沒指定 (null) 則代表永久顯示
    visible_end_datetime = Column(DateTime)

    # 發佈時間，建立這篇最新消息當下的時間
    publication_datetime = Column(DateTime, nullable=False, default=datetime.now)

    # 前台的顯示邏輯是
    # 如果有指定 visible_start_datetime 就以此欄位作為排序依據，否則就是依據 publication_datetime 欄位排序。
    # 試想：如果我在年初就先建立了一個最新消息，並把它排程到年底顯示，那等到年底時，我應該會期待這篇文章會出現在最上面才對
    display_datetime = Column(DateTime, nullable=False, default=datetime.now)

    # 最後更新時間
    last_updated_datetime = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 標籤
    tags = relationship('models.tag.TagModel', secondary=news_tags_association, back_populates='news')

    group_id = Column(Integer, ForeignKey('groups.id'))

    category_id = Column(Integer, ForeignKey('news_categories.id'))


class NewsCategoryModel(BaseObject):
    """最新消息分類"""

    __tablename__ = 'news_categories'

    id = Column(Integer, Identity(always=True), primary_key=True)

    # 分類名稱
    name = Column(String(50), unique=True, nullable=False)

    # 排序
    order = Column(Integer, nullable=False, default=0, server_default='0')

    news = relationship(NewsModel, backref='category')
