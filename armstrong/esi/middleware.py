import hashlib
import re

from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.http import HttpResponse

from .utils import merge_fragment_headers, merge_fragment_cookies, \
    replace_esi_tags


esi_tag_re = re.compile(r'<esi:include src="(?P<url>[^"]+?)"\s*/>', re.I)

class IncludeEsiMiddleware(object):
    def process_response(self, request, response):
        esi_status = getattr(response, '_esi', {'used': False})
        if esi_status['used']:
            replace_esi_tags(request, response)
        return response

class StoreEsiStatusMiddleware(object):
    def process_response(self, request, response):
        if hasattr(request, '_esi'):
            response._esi = request._esi
        return response
