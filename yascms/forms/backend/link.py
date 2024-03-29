from pyramid_wtforms import (Form,
                             StringField,
                             TextAreaField,
                             BooleanField,
                             SelectField,
                             FileField)
from pyramid_wtforms.validators import (InputRequired,
                                        Length,
                                        FileSize,
                                        FileAllowed)


# TODO: 要加上可以選擇分類選單排序的欄位
class LinkForm(Form):
    """好站連結的建立表單"""

    title = StringField('標題*', [InputRequired('標題欄位必填'), Length(max=50, message='最長只接受 50 個字元')])

    url = TextAreaField('網址*', [InputRequired('網址欄位必填')])

    # TODO: 要讓系統可以設定上傳的檔案大小限制，目前寫死必須小於 10 MB
    icon = FileField('圖檔 (150x60)', [FileSize(max=10, base='mb', message='檔案必須小於 10 mb'),
                             FileAllowed(['jpg', 'png'], message='只接受 jpg / png 格式')])

    is_pinned = BooleanField('是否於首頁顯示')

    group_id = SelectField('張貼管理群組', coerce=int)

    category_id = SelectField('分類群組', coerce=int)

    class Meta:
        locales = ['zh_TW', 'tw']


class LinkCategoryForm(Form):
    """好站連結分類表單"""

    name = StringField('名稱*', [InputRequired('名稱必填')])

    # TODO: 要動態產生，目前先寫死 20 組
    order = SelectField('排序', [InputRequired('排序必填')],
                        choices=[(i, str(i)) for i in range(21)],
                        coerce=int)

    class Meta:
        locales = ['zh_TW', 'tw']
