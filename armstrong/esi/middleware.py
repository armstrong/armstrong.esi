import hashlib
import re

from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.http import HttpResponse

from .utils import replace_esi_tags, gzip_response_content, \
    gunzip_response_content


esi_tag_re = re.compile(r'<esi:include src="(?P<url>[^"]+?)"\s*/>', re.I)

class IncludeEsiMiddleware(object):
    def process_response(self, request, response):
        esi_status = getattr(request, '_esi', {'used': False})
        if not esi_status['used']:
            return response

        # There is the possibility that GZipMiddleware has already been loaded by
        # the time we get this.  This is an uncommon case (and one advised against
        # in Django documentation), but when it happens we need to be able to work.
        #
        # Note: Running GZipMiddleware prior to the IncludeEsiMiddleware causes the
        # response to be compressed, decompressed, and then recompressed again.
        # Nine times out of ten, this is **not** what you want, but in the rare
        # instance that it is, this will continue to work as expected.
        is_gzipped = response.get('Content-Encoding', None) == 'gzip'
        if is_gzipped:
            gunzip_response_content(response)

        replace_esi_tags(request, response)

        if is_gzipped:
            gzip_response_content(request, response)

        return response

class StoreEsiStatusMiddleware(object):
    def process_response(self, request, response):
        if hasattr(request, '_esi'):
            response['X-ESI'] = 'true'
        return response
