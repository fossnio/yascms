import re
from markupsafe import Markup, escape


def linkify(text):
    """用來將最新消息裡面的網址加上可點選的超連結"""

    if not text:
        return ""

    safe_text = str(escape(text))

    # 這個正則表達式會匹配 http/https 網址
    url_pattern = r'(https?://[^\s<>"]+)'

    def handle_match(m):
        url = m.group(1)
        # 檢查網址結尾是否有標點符號
        trailing_punctuation = ""
        # 這裡可以根據需求增加想要剔除的結尾符號
        while url and url[-1] in '.,!?;:()，：。？！（）':
            trailing_punctuation = url[-1] + trailing_punctuation
            url = url[:-1]
        return rf'<a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：{url} (另開新視窗)">{url}</a>{trailing_punctuation}'

    processed_text = re.sub(url_pattern, handle_match, safe_text)
    processed_text = processed_text.replace('\n', '<br>')

    return Markup(processed_text)

