from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.http import HttpResponse
import re

from . import http_client


def replace_esi_tags(request, content, urls):
    for url in urls:
        esi_tag = '<esi:include src="%s" />' % url
        client = http_client.Client(cookies=request.COOKIES)
        replacement = client.get(url)
        content = content.replace(esi_tag, replacement.content)
    return content

class BaseEsiMiddleware(object):
    def process_request(self, request):
        request._esi_was_invoked = []

class RequestMiddleware(BaseEsiMiddleware):
    def process_request(self, request):
        super(RequestMiddleware, self).process_request(request)

        data = cache.get(request.get_full_path())
        if not data:
            return None

        content = replace_esi_tags(request, data['content'], data['urls'])
        return HttpResponse(content=content)

class ResponseMiddleware(BaseEsiMiddleware):
    def process_response(self, request, response):
        if request._esi_was_invoked:
            original_content = response.content
            response.content = replace_esi_tags(request, response.content,
                                                request._esi_was_invoked)
            cache.set(request.get_full_path(), {
                'content': original_content,
                'urls': request._esi_was_invoked,
            })
        return response

class EsiMiddleware(RequestMiddleware, ResponseMiddleware):
    pass

