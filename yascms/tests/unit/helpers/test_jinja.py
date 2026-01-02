from yascms.helpers.jinja import linkify


def test_linkify_should_transform_url_to_html_a_tag():
    assert (linkify('測試http://www.google.com') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>')
    assert (linkify('測試http://www.google.com.') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>.')
    assert (linkify('測試http://www.google.com。') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>。')
    assert (linkify('測試http://www.google.com(') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>(')
    assert (linkify('測試http://www.google.com)') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>)')
    assert (linkify('測試http://www.google.com（') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>（')
    assert (linkify('測試http://www.google.com）') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>）')
    assert (linkify('臺北市本土語文教學資源網（https://pthg.tp.edu.tw），學生登錄後應輸入學校') == '臺北市本土語文教學資源網（<a href="https://pthg.tp.edu.tw" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：https://pthg.tp.edu.tw (另開新視窗)">https://pthg.tp.edu.tw</a>），學生登錄後應輸入學校')

