from django.core import urlresolvers
from django.core.cache import cache
from django.http import HttpResponse
import re

class BaseEsiMiddleware(object):
    def __init__(self, resolver=urlresolvers):
        self.resolver = resolver

    def process_request(self, request):
        request._esi_was_invoked = False

class RequestMiddleware(BaseEsiMiddleware):
    def process_request(self, request):
        super(RequestMiddleware, self).process_request(request)

        data = cache.get(request.get_full_path())
        if not data:
            return None

        for url, (view, args, kwargs) in data['urls'].items():
            esi_tag = '<esi:include src="%s" />' % url
            replacement = view(request, *args, **kwargs)
            data['content'] = data['content'].replace(esi_tag, str(replacement))

        return HttpResponse(content=data['content'])

class ResponseMiddleware(BaseEsiMiddleware):
    def process_response(self, request, response):
        if request._esi_was_invoked:
            esi_urls = re.findall(r'<esi:include src="([^"]+)" />', response.content)
            urls = {}
            original_content = response.content
            for url in esi_urls:
                (view, args, kwargs) = self.resolver.resolve(url)
                urls[url] = (view, args, kwargs)
                new_content = view(request, *args, **kwargs)
                esi_tag = '<esi:include src="%s" />' % url
                response.content = response.content.replace(esi_tag, str(new_content))
            cache.set(request.get_full_path(), {
                'content': original_content,
                'urls': urls,
            })
        return response

class EsiMiddleware(RequestMiddleware, ResponseMiddleware):
    pass

