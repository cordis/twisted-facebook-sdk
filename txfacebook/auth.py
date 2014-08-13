import urllib
import hashlib
import hmac
import base64

from txfacebook.imports import json, inlineCallbacks, returnValue
from txfacebook.graph import GraphAPI
from txfacebook.exceptions import GraphAPIError


@inlineCallbacks
def get_user_from_cookie(cookies, app_id, secret):
    """
    Parses the cookie set by the official Facebook JavaScript SDK.

    cookies should be a dictionary-like object mapping cookie names to
    cookie values.

    If the user is logged in via Facebook, we return a dictionary with
    the keys 'uid' and 'access_token'. The former is the user's
    Facebook ID, and the latter can be used to make authenticated
    requests to the Graph API. If the user is not logged in, we
    return None.

    Download the official Facebook JavaScript SDK at
    http://github.com/facebook/connect-js/. Read more about Facebook
    authentication at
    http://developers.facebook.com/docs/authentication/.

    :type app_id: C{str}
    :type secret: C{str}
    :rtype: C{dict} or C{None}
    """
    cookie = cookies.get('fbsr_' + app_id, '')
    if not cookie:
        returnValue(None)

    parsed_request = parse_signed_request(cookie, secret)
    if not parsed_request:
        returnValue(None)

    try:
        ret = yield get_access_token_from_code(parsed_request['code'], '', app_id, secret)
    except GraphAPIError:
        returnValue(None)
    else:
        ret['uid'] = parsed_request['user_id']
        returnValue(ret)


def parse_signed_request(signed_request, secret):
    """
    Return dictionary with signed request data.

    We return a dictionary containing the information in the
    signed_request. This includes a user_id if the user has authorised
    your application, as well as any information requested.

    If the signed_request is malformed or corrupted, False is returned.

    :type signed_request: C{unicode}
    :type secret: C{str}
    :rtype: C{dict}
    """
    def decode_string(encoded_string):
        return base64.urlsafe_b64decode(encoded_string + '=' * ((4 - len(encoded_string) % 4) % 4))

    try:
        encoded_signature, encoded_data = map(str, signed_request.split('.', 1))
        signature = decode_string(encoded_signature)
        data = decode_string(encoded_data)
    except IndexError:
        # Signed request was malformed.
        return False
    except TypeError:
        # Signed request had a corrupted encoded_data.
        return False

    data = json.loads(data)
    if data.get('algorithm', '').upper() != 'HMAC-SHA256':
        return False

    # HMAC can only handle ascii (byte) strings
    # http://bugs.python.org/issue5285
    secret = secret.encode('ascii')
    encoded_data = encoded_data.encode('ascii')

    expected_signature = hmac.new(secret, msg=encoded_data, digestmod=hashlib.sha256).digest()
    if signature != expected_signature:
        return False

    return data


def auth_url(app_id, canvas_url, scope_list=None, **kwargs):
    url = 'https://www.facebook.com/dialog/oauth?'
    params = {
        'client_id': app_id,
        'redirect_uri': canvas_url
    }
    if scope_list:
        params['scope'] = ','.join(scope_list)
    params.update(kwargs)
    return url + urllib.urlencode(params)


def get_access_token_from_code(code, redirect_uri, app_id, secret):
    return GraphAPI().get_access_token_from_code(code, redirect_uri, app_id, secret)


def get_app_access_token(app_id, secret):
    return GraphAPI().get_app_access_token(app_id, secret)
