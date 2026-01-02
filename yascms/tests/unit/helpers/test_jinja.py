from yascms.helpers.jinja import linkify


def test_linkify_should_transform_url_to_html_a_tag():
    assert (linkify('測試http://www.google.com') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>')
    assert (linkify('測試http://www.google.com.') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>.')
    assert (linkify('測試http://www.google.com。') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>。')
    assert (linkify('測試http://www.google.com(') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>(')
    assert (linkify('測試http://www.google.com)') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>)')
    assert (linkify('測試http://www.google.com（') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>（')
    assert (linkify('測試http://www.google.com）') == '測試<a href="http://www.google.com" target="_blank" rel="noopener noreferrer" aria-label="前往網頁：http://www.google.com (另開新視窗)">http://www.google.com</a>）')
