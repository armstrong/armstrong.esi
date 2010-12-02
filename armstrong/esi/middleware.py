import hashlib
import re

from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDict

from . import http_client
from ._utils import merge_fragment_headers, merge_fragment_cookies, \
    HEADERS_TO_MERGE


esi_tag_re = re.compile(r'<esi:include src="(?P<url>[^"]+?)"\s*/>', re.I)

def replace_esi_tags(request, response, urls):
    if not urls:
        return

    fragment_headers = MultiValueDict()
    fragment_cookies = []
    request_data = {
        'cookies': request.COOKIES,
        'HTTP_REFERER': request.build_absolute_uri(),
    }

    for url in urls:
        esi_tag = '<esi:include src="%s" />' % url
        client = http_client.Client(**request_data)
        fragment = client.get(url)
        response.content = response.content.replace(esi_tag, fragment.content)

        for header in HEADERS_TO_MERGE:
            if header in fragment:
                fragment_headers.appendlist(header, fragment[header])
        if fragment.cookies:
            fragment_cookies.append(fragment.cookies)

    merge_fragment_headers(response, fragment_headers)
    merge_fragment_cookies(response, fragment_cookies)

class BaseEsiMiddleware(object):
    def process_request(self, request):
        request._esi_fragment_urls = []

class IncludeEsiMiddleware(BaseEsiMiddleware):
    def process_response(self, request, response):
        content_hash = hashlib.sha1(response.content).hexdigest()
        cache_key = 'armstrong.esi.%s' % content_hash

        urls = getattr(request, '_esi_fragment_urls', None)
        if urls:
            cache.set(cache_key, urls)
        else:
            # TODO: All pages without ESI tags will still require a cache
            # lookup and searching the content for ESI tags. Avoiding this
            # with a header that indicates the presence or lack of ESI tags
            # when we're certain in advance could be useful.
            urls = cache.get(cache_key)
            if urls is None:
                # Parsing HTML with regular expressions is Wrong, but it will
                # suffice for finding the ESI tags placed by our templatetag.
                matches = esi_tag_re.finditer(response.content)
                urls = [match.group('url') for match in matches]
                cache.set(cache_key, urls)

        replace_esi_tags(request, response, urls)
        return response
