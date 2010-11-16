from django.core import urlresolvers
from django.core.cache import cache
import re

class BaseEsiMiddleware(object):
    def process_request(self, request):
        request._esi_was_invoked = False

class ResponseMiddleware(object):
    def __init__(self, resolver=urlresolvers):
        self.resolver = resolver

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
                'contents': original_content,
                'urls': urls,
            })
        return response
