from pyramid_sqlalchemy import BaseObject
from sqlalchemy import (Column,
                        Integer,
                        String)
from sqlalchemy.schema import Identity
from sqlalchemy.orm import relationship

from yascms.models.association import news_tags_association, pages_tags_association


class TagModel(BaseObject):
    """標籤"""

    __tablename__ = 'tags'

    id = Column(Integer, Identity(always=True), primary_key=True)

    name = Column(String(50), unique=True, nullable=False)

    def __str__(self):
        return self.name

    news = relationship('models.news.NewsModel', secondary=news_tags_association, back_populates='tags')
    pages = relationship('models.page.PageModel', secondary=pages_tags_association, back_populates='tags')
