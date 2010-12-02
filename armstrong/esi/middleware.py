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
        content_hash = hashlib.sha1(response.content).hexdigest()
        cache_key = 'armstrong.esi.%s' % content_hash

        esi_status = getattr(request, '_esi', {'used': False})
        if esi_status['used']:
            cache.set(cache_key, esi_status)
        else:
            # TODO: All pages without ESI tags will still require a cache
            # lookup and searching the content for ESI tags. Avoiding this
            # with a header that indicates the presence or lack of ESI tags
            # when we're certain in advance could be useful.
            esi_status = cache.get(cache_key)
            if esi_status is None:
                # Parsing HTML with regular expressions is Wrong, but it will
                # suffice for finding the ESI tags placed by our templatetag.
                esi_status = {'used': bool(esi_tag_re.search(response.content))}
                cache.set(cache_key, esi_status)

        if esi_status['used']:
            replace_esi_tags(request, response)
        return response
