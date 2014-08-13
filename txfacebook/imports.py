try:
    import json
except ImportError:
    import simplejson as json

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

try:
    from twisted.internet.defer import Deferred, inlineCallbacks, maybeDeferred, returnValue
except ImportError:
    from deferred import Deferred, inlineCallbacks, maybeDeferred, returnValue

from treq import request

__all__ = ['json', 'parse_qs', 'inlineCallbacks', 'maybeDeferred', 'returnValue', 'Deferred', 'request']
