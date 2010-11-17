from django.core import urlresolvers
from django.core.cache import cache
from django.http import HttpResponse
import re

class BaseEsiMiddleware(object):
    def process_request(self, request):
        request._esi_was_invoked = []

class RequestMiddleware(BaseEsiMiddleware):
    def process_request(self, request):
        super(RequestMiddleware, self).process_request(request)

        data = cache.get(request.get_full_path())
        if not data:
            return None

        for url, (view, args, kwargs) in data['urls'].items():
            esi_tag = '<esi:include src="%s" />' % url
            replacement = view(request, *args, **kwargs)
            data['content'] = data['content'].replace(esi_tag, replacement.content)

        return HttpResponse(content=data['content'])

class ResponseMiddleware(BaseEsiMiddleware):
    def __init__(self, resolver=urlresolvers):
        self.resolver = resolver

    def process_response(self, request, response):
        if request._esi_was_invoked:
            urls = {}
            original_content = response.content
            for url in request._esi_was_invoked:
                (view, args, kwargs) = self.resolver.resolve(url)
                urls[url] = (view, args, kwargs)
                new_content = view(request, *args, **kwargs)
                esi_tag = '<esi:include src="%s" />' % url
                response.content = response.content.replace(esi_tag, new_content.content)
            cache.set(request.get_full_path(), {
                'content': original_content,
                'urls': urls,
            })
        return response

class EsiMiddleware(RequestMiddleware, ResponseMiddleware):
    pass

