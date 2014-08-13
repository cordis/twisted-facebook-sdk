#!/usr/bin/env python

# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Python client library for the Facebook Platform.

This client library is designed to support the Graph API and the
official Facebook JavaScript SDK, which is the canonical way to
implement Facebook authentication. Read more about the Graph API at
http://developers.facebook.com/docs/api. You can download the Facebook
JavaScript SDK at http://github.com/facebook/connect-js/.

If your application is using Google AppEngine's webapp framework, your
usage of this module might look like this:

user = facebook.get_user_from_cookie(self.request.cookies, key, secret)
if user:
    graph = facebook.GraphAPI(user['access_token'])
    profile = yield graph.get_object('me')
    friends = yield graph.get_connections('me', 'friends')

"""


from txfacebook.exceptions import GraphAPIError
from txfacebook.imports import (
    parse_qs,
    json,
    returnValue,
    inlineCallbacks,
    maybeDeferred,
    request as request_func
)


class GraphAPI(object):
    """A client for the Facebook Graph API.

    See http://developers.facebook.com/docs/api for complete
    documentation for the API.

    The Graph API is made up of the objects in Facebook (e.g., people,
    pages, events, photos) and the connections between them (e.g.,
    friends, photo tags, and event RSVPs). This client provides access
    to those primitive types in a generic way. For example, given an
    OAuth access token, this will fetch the profile of the active user
    and the list of the user's friends:

       graph = facebook.GraphAPI(access_token)
       user = yield graph.get_object('me')
       friends = yield graph.get_connections(user['id'], 'friends')

    You can see a list of all of the objects and connections supported
    by the API at http://developers.facebook.com/docs/reference/api/.

    You can obtain an access token via OAuth or by using the Facebook
    JavaScript SDK. See
    http://developers.facebook.com/docs/authentication/ for details.

    If you are using the JavaScript SDK, you can use the
    get_user_from_cookie() method below to get the OAuth access token
    for the active user from the cookie saved by the SDK.

    """
    endpoint = 'https://graph.facebook.com/v2.1/'

    def __init__(self, access_token=None, timeout=15):
        self.access_token = access_token
        self.timeout = timeout

    def get_object(self, object_id, **args):
        """
        Fetches the given object from the graph.

        :type object_id: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        return self.request(object_id, args)

    def get_objects(self, object_id_list, **args):
        """
        Fetches all of the given object from the graph.
        We return a map from ID to object. If any of the IDs are
        invalid, we raise an exception.

        :type object_id_list: C{list} of C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        args['ids'] = ','.join(object_id_list)
        return self.request('', args)

    def get_connections(self, object_id, connection_name, **args):
        """
        Fetches the connections for given object

        :type object_id: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        return self.request(object_id + '/' + connection_name, args)

    def put_wall_post(self, message, attachment=None, profile_id='me'):
        """
        Writes a wall post to the given profile's wall.

        We default to writing to the authenticated user's wall if no
        profile_id is specified.

        attachment adds a structured attachment to the status message
        being posted to the Wall. It should be a dictionary of the form:

            {'name': 'Link name'
             'link': 'http://www.example.com/',
             'caption': '{*actor*} posted a new review',
             'description': 'This is a longer description of the attachment',
             'picture': 'http://www.example.com/thumbnail.jpg'}

        :type message: C{unicode}
        :type attachment: C{dict} optional
        :type profile_id: C{str} optional
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        attachment = attachment or {}
        return self.put_object(profile_id, 'feed', message=message, **attachment)

    def put_comment(self, object_id, message):
        """
        Writes the given comment on the given post.

        :type object_id: C{str}
        :type message: C{unicode}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        return self.put_object(object_id, 'comments', message=message)

    def put_like(self, object_id):
        """Likes the given post."""
        return self.put_object(object_id, 'likes')

    def put_object(self, parent_object_id, connection_name, **data):
        """
        Writes the given object to the graph, connected to the given parent.

        For example,

            graph.put_object('me', 'feed', message='Hello, world')

        writes 'Hello, world' to the active user's wall. Likewise, this
        will comment on a the first post of the active user's feed:

            feed = yield graph.get_connections('me', 'feed')
            post = feed['data'][0]
            graph.put_object(post['id'], 'comments', message='First!')

        See http://developers.facebook.com/docs/api#publishing for all
        of the supported writeable objects.

        Certain write operations require extended permissions. For
        example, publishing to a user's feed requires the
        'publish_actions' permission. See
        http://developers.facebook.com/docs/publishing/ for details
        about publishing permissions.

        :type object_id: C{str}
        :type connection_name: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        return self.request(parent_object_id + '/' + connection_name, body=data, method='POST')

    def delete_object(self, object_id):
        """
        Deletes the object with the given ID from the graph.

        :type object_id: C{str}
        :rtype: L{txfacebook.imports.Deferred}
        """
        return self.request(object_id, method='DELETE')

    def delete_request(self, user_id, request_id):
        """
        Deletes the Request with the given ID for the given user.

        :type user_id: C{str}
        :type request_id: C{str}
        :rtype: L{txfacebook.imports.Deferred}
        """
        return self.request('%s_%s' % (request_id, user_id), method='DELETE')

    def put_photo(self, image, caption=None, object_id='me', **kwargs):
        """
        Uploads an image using multipart/form-data.

        :type image: C{file}
        :type caption: C{unicode} optional
        :type object_id: C{str} optional
        :rtype: L{txfacebook.imports.Deferred}
        """
        kwargs.update({'message': caption})
        return self.request(object_id, body=kwargs, files={'file': image}, method='POST')

    @inlineCallbacks
    def get_app_access_token(self, app_id, secret):
        """
        Get the application's access token as a string.

        :type app_id: C{str}
        :type secret: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{str}
        """
        response = yield self.request('oauth/access_token', args={
            'grant_type': 'client_credentials',
            'client_id': app_id,
            'client_secret': secret
        })
        returnValue(response['access_token'])

    def get_access_token_from_code(self, code, redirect_uri, app_id, secret):
        """
        Get an access token from the 'code' returned from an OAuth dialog.

        Returns a dict containing the user-specific access token and its
        expiration date (if applicable).

        :type code: C{str}
        :type redirect_uri: C{str}
        :type app_id: C{str}
        :type secret: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{dict}
        """
        return self.request('oauth/access_token', {
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': app_id,
            'client_secret': secret
        })

    def extend_access_token(self, app_id, secret):
        """
        Extends the expiration time of a valid OAuth access token. See
        <https://developers.facebook.com/roadmap/offline-access-removal/#extend_token>

        :type app_id: C{str}
        :type secret: C{str}
        :rtype: L{txfacebook.imports.Deferred} of C{str}
        """
        return self.request('access_token', {
            'client_id': app_id,
            'client_secret': secret,
            'grant_type': 'fb_exchange_token',
            'fb_exchange_token': self.access_token,
        })

    @inlineCallbacks
    def request(self, path, args=None, body=None, files=None, method='GET', timeout=None):
        """
        Fetches the given path in the Graph API.

        We translate args to a valid query string. If post_args is
        given, we send a POST request to the given path with the given
        arguments.
        """
        if method != 'GET':
            assert self.access_token, 'Write operations require an access token'

        args, body = self._prepare_args_and_body(args, body)
        response = yield self._do_request(method, path, args, body, files, timeout or self.timeout)
        ret = yield self._parse_response(response)
        returnValue(ret)

    def _prepare_args_and_body(self, body, args):
        args = args or {}

        if self.access_token:
            if body is not None:
                body['access_token'] = self.access_token
            else:
                args['access_token'] = self.access_token

        return body, args

    @inlineCallbacks
    def _do_request(self, method, path, args, body, files, timeout):
        kwargs = dict(timeout=timeout, params=args, data=body, files=files)
        response = yield maybeDeferred(request_func, method, self.endpoint + path, **kwargs)
        returnValue(response)

    @staticmethod
    @inlineCallbacks
    def _parse_response(response):
        content_type = response.headers.getRawHeaders('content-type')[0]
        if 'image/' in content_type:
            response_content = yield response.content()
            ret = {
                'data': response_content,
                'mime-type': content_type,
                'url': response.url
            }
        elif 'json' in content_type or 'javascript' in content_type:
            ret = yield response.json()
        else:
            response_text = yield response.text()
            query_string = parse_qs(response_text)
            if 'access_token' in query_string:
                if 'access_token' in query_string:
                    ret = {
                        'access_token': query_string['access_token'][0]
                    }
                    if 'expires' in query_string:
                        ret['expires'] = query_string['expires'][0]
                else:
                    ret = json.loads(response_text)
                    raise GraphAPIError(ret)
            else:
                raise GraphAPIError('Maintype was not text, image, or querystring')

        if ret and isinstance(ret, dict) and ret.get('error'):
            raise GraphAPIError(ret)

        returnValue(ret)
