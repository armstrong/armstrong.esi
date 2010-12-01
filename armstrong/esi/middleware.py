from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDict
import re

from . import http_client
from ._utils import merge_fragment_headers, merge_fragment_cookies, \
    HEADERS_TO_MERGE


def replace_esi_tags(request, response, urls):
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

class RequestMiddleware(BaseEsiMiddleware):
    def process_request(self, request):
        super(RequestMiddleware, self).process_request(request)

        data = cache.get(request.get_full_path())
        if not data:
            return None

        response = HttpResponse(content=data['content'])
        replace_esi_tags(request, response, data['urls'])
        return response

class ResponseMiddleware(BaseEsiMiddleware):
    def process_response(self, request, response):
        if request._esi_fragment_urls:
            original_content = response.content
            replace_esi_tags(request, response, request._esi_fragment_urls)
            cache.set(request.get_full_path(), {
                'content': original_content,
                'urls': request._esi_fragment_urls,
            })
        return response

class EsiMiddleware(RequestMiddleware, ResponseMiddleware):
    pass

