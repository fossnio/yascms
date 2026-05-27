import json
import base64
import logging

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from authlib.integrations.requests_client import OAuth2Session

from yascms.views.frontend.login import create_credential
from yascms.dal import DAL


logger = logging.getLogger(__name__)


def oauth2_google_login_factory(request, provider_name, provider_config):
    """Google OAuth2 login 實作
    Args:
        request: pyramid.request.Request
        provider_name: provider 名稱，都小寫
        provider_config: Google 相關的設定值

    Returns:
        回傳重導的網址
    """
    scope = ['openid',
             'https://www.googleapis.com/auth/userinfo.profile',
             'https://www.googleapis.com/auth/userinfo.email',
             'https://www.googleapis.com/auth/admin.directory.group']
    session = OAuth2Session(provider_config['settings']['client_id'],
                            provider_config['settings']['client_secret'],
                            scope=' '.join(scope),
                            redirect_uri=request.route_url('oauth2_provider_callback', provider_name=provider_name))
    uri, state = session.create_authorization_url(provider_config['authorization_url'])
    session.close()
    return HTTPFound(location=uri)


def oauth2_provider_login_factory(request, provider_name, provider_config):
    """根據傳入的 provider_name 回傳對應的 provider login 重導網址

    Args:
        request: pyramid.request.Request
        provider_name: provider 名稱，都是小寫
        provider_config: provider 對應的設定值

    Returns:
        回傳對應的 provider login factory 的結果，若找不到對應的 provider 則回傳 403
    """
    if provider_name == 'google':
        return oauth2_google_login_factory(request, provider_name, provider_config)
    logger.error('找不到 OAuth2 provider %s', provider_name)
    raise HTTPNotFound()


@view_config(route_name='oauth2_provider_login')
def oauth2_provider_login_view(request):
    """各 OAuth2 Provider 的 login 進入點"""
    provider_name = request.matchdict['provider_name']
    oauth2_integration_config = DAL.get_oauth2_integration_config()
    if (provider_name in oauth2_integration_config
        and oauth2_integration_config[provider_name]['settings']['enabled']):

        return oauth2_provider_login_factory(request, provider_name, oauth2_integration_config[provider_name])
    return HTTPForbidden()


def oauth2_google_callback_factory(request, provider_name, provider_config):
    """Google OAuth2 callback 實作
    Args:
        request: pyramid.request.Request
        provider_name: provider 名稱，都小寫
        provider_config: Google 相關的設定值

    Returns:
        若找到對應的使用者回傳認証完的結果，若找不到則傳回 404
    """
    code = request.GET['code']
    state = request.GET['state']
    callback_url = request.current_route_url(code=code, state=state)
    scope = ['openid',
             'https://www.googleapis.com/auth/userinfo.profile',
             'https://www.googleapis.com/auth/userinfo.email',
             'https://www.googleapis.com/auth/admin.directory.group']
    session = OAuth2Session(provider_config['settings']['client_id'],
                            provider_config['settings']['client_secret'],
                            scope=' '.join(scope),
                            redirect_uri=request.route_url('oauth2_provider_callback', provider_name=provider_name))
    token = session.fetch_token(provider_config['access_token_uri'], authorization_response=callback_url)
    session.close()
    b64_payload = token['id_token'].split('.')[1]
    b64_padding_payload = b64_payload + "=" * ((4 - len(b64_payload) % 4) % 4)
    jwt_payload = json.loads(base64.b64decode(b64_padding_payload, '-_').decode('utf8'))
    user = DAL.get_user_from_email(jwt_payload['email'])
    if user:
        result = create_credential(request, user, provider_name)
        logger.info('使用者 %s%s 透過 Google OAuth2 以 email %s 成功登入', user.last_name, user.first_name, user.email)
        return result
    msg = f"Google OAuth2 認証異常：Email {jwt_payload['email']} 找不到對應的使用者"
    logger.warning(msg)
    request.session.flash(msg, 'fail')
    return HTTPFound(location=request.route_url('login'))


def oauth2_provider_callback_factory(request, provider_name, provider_config):
    """根據傳入的 provider_name 呼叫對應的 provider callback factory 處理

    Args:
        request: pyramid.request.Request
        provider_name: provider 名稱，都是小寫
        provider_config: provider 對應的設定值

    Returns:
        回傳對應的 provider callback 結果，若找不到對應的 provider 則回傳 403
    """
    if provider_name == 'google':
        return oauth2_google_callback_factory(request, provider_name, provider_config)
    logger.error('找不到 OAuth2 provider %s 的 callback', provider_name)
    raise HTTPNotFound()


@view_config(route_name='oauth2_provider_callback')
def oauth2_provider_callback_view(request):
    """各 OAuth2 Provider 的 callback 進入點"""
    provider_name = request.matchdict['provider_name']
    oauth2_integration_config = DAL.get_oauth2_integration_config()
    if (provider_name in oauth2_integration_config
        and oauth2_integration_config[provider_name]['settings']['enabled']):

        return oauth2_provider_callback_factory(request, provider_name, oauth2_integration_config[provider_name])
    else:
        raise HTTPNotFound()
