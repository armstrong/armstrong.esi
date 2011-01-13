from cStringIO import StringIO
from email.utils import parsedate
import gzip
import logging
import re
import time
from urlparse import urljoin

from django.conf import settings
from django.http import HttpResponse
from django.middleware.gzip import GZipMiddleware
from django.utils.cache import cc_delim_re
from django.utils.datastructures import MultiValueDict
from django.utils.http import http_date

from . import http_client

try:
    from logging import NullHandler
except ImportError:
    # Compatibility mode for 2.6.x
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass


log = logging.getLogger('armstrong.esi')
log.addHandler(NullHandler())
esi_tag_re = re.compile(r'<esi:include src="(?P<url>[^"]+?)"\s*/>', re.I)

def reduce_vary_headers(response, additional):
    '''Merges the Vary header values so all headers are included.'''
    original = response.get('Vary', None)
    if original is not None:
        additional.append(original)
    # Keep track of normalized, lowercase header names in seen_headers while
    # maintaining the order and case of the header names in final_headers.
    seen_headers = set()
    final_headers = []
    for vary_value in additional:
        headers = cc_delim_re.split(vary_value)
        for header in headers:
            if header.lower() in seen_headers:
                continue
            seen_headers.add(header.lower())
            final_headers.append(header)
    response['Vary'] = ', '.join(final_headers)

def reduce_last_modified_headers(response, additional):
    '''Sets Last-Modified to the latest of all of the header values.'''
    dates = additional
    if 'Last-Modified' in response:
        dates.append(response['Last-Modified'])
    dates = [time.mktime(parsedate(date_str)) for date_str in dates]
    latest = max(dates)
    response['Last-Modified'] = http_date(latest)

HEADERS_TO_MERGE = {
    'Vary': reduce_vary_headers,
    'Last-Modified': reduce_last_modified_headers,
}

def merge_fragment_headers(response, fragment_headers):
    '''
    Given fragment_headers, a MultiValueDict or other mapping of header names to
    values, add the header values to the response as appropriate.
    '''
    for header, reduce_func in HEADERS_TO_MERGE.items():
        if not header in fragment_headers:
            continue
        if hasattr(fragment_headers, 'getlist'):
            values = fragment_headers.getlist(header)
        else:
            value = fragment_headers.get(header)
            values = [value] if value is not None else []
        reduce_func(response, values)

def merge_fragment_cookies(response, fragment_cookies):
    '''
    Merges the fragment and response cookies.

    Set the fragment cookies in the order they occurred, then set the main
    response cookie last.
    '''
    if not fragment_cookies:
        return
    cookies = fragment_cookies[0]
    cookies_to_reduce = fragment_cookies[1:]
    cookies_to_reduce.append(response.cookies)
    for cookie_obj in cookies_to_reduce:
        for key, morsel in cookie_obj.items():
            # To set Morsels as cookie values directly, we need to bypass
            # BaseCookie.__setitem__.
            dict.__setitem__(cookies, key, morsel)
    response.cookies = cookies

def gunzip_response_content(response):
    '''
    If the response has already been compressed, gunzip it so we can modify
    the text.
    '''
    f = gzip.GzipFile(fileobj=StringIO(response.content))
    response.content = f.read()
    f.close()
    del response['Content-Encoding']

def gzip_response_content(request, response):
    GZipMiddleware().process_response(request, response)

def build_full_fragment_url(request, url):
    if url.startswith('/'):
        return url
    else:
        return urljoin(request.path, url)

# TODO: Test this independently of the middleware
# TODO: Reduce the lines of codes and varying functionality of this code so its
#       tests can be reduced in complexity.
def replace_esi_tags(request, response):
    process_errors = getattr(settings, 'ESI_PROCESS_ERRORS', False)
    fragment_headers = MultiValueDict()
    fragment_cookies = []
    request_data = {
        'cookies': request.COOKIES,
        'HTTP_REFERER': request.build_absolute_uri(),
        'HTTP_X_ESI_FRAGMENT': True,
    }

    replacement_offset = 0
    for match in esi_tag_re.finditer(response.content):
        url = build_full_fragment_url(request, match.group('url'))

        if response.status_code == 200 or process_errors:
            client = http_client.Client(**request_data)
            fragment = client.get(url)
        else:
            fragment = HttpResponse()

        if fragment.status_code != 200:
            # Remove the error content so it isn't added to the page.
            fragment.content = ''
            extra = {'data': {
                'fragment': fragment.__dict__,
                'request': request.__dict__,
            }}
            log.error('ESI fragment %s returned status code %s' %
                (url, fragment.status_code), extra=extra)

        start = match.start() + replacement_offset
        end = match.end() + replacement_offset
        response.content = '%s%s%s' % (response.content[:start],
            fragment.content, response.content[end:])
        replacement_offset += len(fragment.content) - len(match.group(0))

        for header in HEADERS_TO_MERGE:
            if header in fragment:
                fragment_headers.appendlist(header, fragment[header])
        if fragment.cookies:
            fragment_cookies.append(fragment.cookies)

    merge_fragment_headers(response, fragment_headers)
    merge_fragment_cookies(response, fragment_cookies)
