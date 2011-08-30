from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.middleware.gzip import GZipMiddleware
from django.utils.cache import cc_delim_re
from django.utils.http import http_date
import fudge
import hashlib
import itertools
import math
import random
import re
import urllib

from ._utils import TestCase
from ._utils import with_fake_request
from .esi_support.views import recursive_404

from .. import middleware
from ..middleware import IncludeEsiMiddleware, EsiHeaderMiddleware
from ..utils import gunzip_response_content


MIDDLEWARES = [
    'armstrong.esi.middleware.IncludeEsiMiddleware',
    'armstrong.esi.middleware.EsiHeaderMiddleware',
]

def full_process_response(request, response, gzip=False):
    if gzip:
        response = GZipMiddleware().process_response(request, response)
    response = EsiHeaderMiddleware().process_response(request, response)
    response = IncludeEsiMiddleware().process_response(request, response)
    return response

def patch_settings(new_settings):
    patches = []
    added_settings = []
    for key, value in new_settings.items():
        if hasattr(settings, key):
            patches.append(fudge.patcher.patch_object(settings, key, value))
        else:
            setattr(settings, key, value)
            added_settings.append(key)
    return patches, added_settings

def restore_settings(patches, added_settings):
    for patch in patches:
        patch.restore()
    for setting in added_settings:
        delattr(settings, setting)

class TestMiddleware(TestCase):
    @with_fake_request
    def test_returns_unmodified_response_on_non_esi_response(self, request):
        original_content = str(random.randint(1000, 2000))
        response = HttpResponse(original_content)
        new_response = full_process_response(request, response)
        self.assertEqual(original_content, new_response.content)

    @with_fake_request
    def test_replaces_esi_tags_with_actual_response(self, request):
        rand = random.randint(100, 200)
        url = '/hello/%d/' % rand

        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        request.has_attr(_esi={'used': True})

        response = HttpResponse()
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        result = full_process_response(request, response)
        self.assertFalse(re.search(esi_tag, result.content), msg='sanity check')
        self.assertEquals(result.content, str(rand))

    @with_fake_request
    def test_replaces_esi_tags_in_gzipped_response(self, request):
        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        request.has_attr(_esi={'used': True})
        request.has_attr(META={'HTTP_ACCEPT_ENCODING': 'gzip'})

        response = HttpResponse()
        esi_tag = '<esi:include src="/500chars/" />'
        response.content = '%s%s%s' % ('z' * 250, esi_tag, 'z' * 250)

        result = full_process_response(request, response, gzip=True)
        self.assertFalse(re.search(esi_tag, result.content), msg='sanity check')
        self.assertTrue(result.get('Content-Encoding', None) == 'gzip')

        gunzip_response_content(result)
        self.assertTrue(re.search('a' * 500, result.content))

    @with_fake_request
    def test_replaces_relative_url_esi(self, request):
        rand = random.randint(100, 200)
        url = './%d/' % rand

        request.has_attr(path='/hello/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        request.has_attr(_esi={'used': True})

        response = HttpResponse()
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag
        fudge.clear_calls()

        result = full_process_response(request, response)
        self.assertFalse(re.search(esi_tag, result.content), msg='sanity check')
        self.assertEquals(result.content, str(rand))

    @with_fake_request
    def check_content_permutation(self, request, permutation, chunk_results):
        request_url = '/page-with-esi-tags/'
        request.has_attr(_esi={'used': True})
        request.provides('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)

        response = HttpResponse(''.join(permutation))
        expected_result = ''.join(chunk_results[chunk] for chunk in permutation)
        result = full_process_response(request, response)
        self.assertEqual(result.content, expected_result)

    # TODO: This is a slow test that should be adjusted for so it doesn't take up
    #       > 80% of the execution time.
    def test_replaces_multiple_esi_tags_correctly(self):
        static_text_options = (
            '',  # Allow ESI tags to end up next to each other
            'abcdefg',
            'abcdefghijklmnopqrstuvwxyz' * 10,
        )
        main_page_chunks = dict(zip(static_text_options, static_text_options))

        # Make sure some of the includes generate content longer than the ESI
        # tag itself and some shorter.
        number_lengths = (1, 10, 50, 100)
        for length in number_lengths:
            num = random.randint(math.pow(10, length-1), math.pow(10, length) - 1)
            content = '<esi:include src="/hello/%s/" />' % num
            main_page_chunks[content] = str(num)

        for permutation in itertools.permutations(main_page_chunks, 4):
            self.check_content_permutation(permutation, main_page_chunks)

    def get_cookie_test_objs(self, request):
        number = random.randint(100, 200)
        fragment_url = '/cookies/%d/' % number
        request_url = '/page-with-esi-tag/'
        response = HttpResponse('<esi:include src="%s" />' % fragment_url)
        request.has_attr(_esi={'used': True})
        request.provides('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)
        return request, response, number

    @with_fake_request
    def test_merges_cookies(self, request):
        request, response, number = self.get_cookie_test_objs(request)
        result = full_process_response(request, response)

        self.assertEqual(result.cookies['a'].value, 'apple')
        self.assertEqual(result.cookies['b'].value, 'banana')
        self.assertEqual(result.cookies['number'].value, str(number))
        self.assertEqual(result.cookies['b']['path'], '/cookies/')

    @with_fake_request
    def test_main_response_cookies_take_precedence(self, request):
        request, response, number = self.get_cookie_test_objs(request)
        response.set_cookie('a', 'alligator')
        result = full_process_response(request, response)

        self.assertEqual(result.cookies['a'].value, 'alligator')

    @with_fake_request
    def check_if_max_time_is_last_modified(self, request, main_response_time,
      fragment_time_1, fragment_time_2, max_time):
        fragment_urls = ['/last-modified/%s/' % num for num in
            (fragment_time_1, fragment_time_2)]
        html = '\n'.join('<esi:include src="%s" />' % url for url in
            fragment_urls)
        response = HttpResponse(html)
        response['Last-Modified'] = http_date(main_response_time)

        request_url = '/page-with-esi-tags/'
        request.has_attr(_esi={'used': True})
        request.provides('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)

        response = full_process_response(request, response)
        self.assertTrue(response['Last-Modified'], max_time)

    def test_merges_last_modified(self):
        time_a = random.randint(10000, 20000)
        time_b = random.randint(40000, 50000)
        time_c = random.randint(60000, 70000)

        max_time = http_date(time_c)
        self.check_if_max_time_is_last_modified(time_a, time_b, time_c, max_time)
        self.check_if_max_time_is_last_modified(time_b, time_c, time_a, max_time)
        self.check_if_max_time_is_last_modified(time_c, time_a, time_b, max_time)

    @with_fake_request
    def check_merged_vary_header(self, request, main_header, fragment_header_1,
      fragment_header_2):
        fragment_urls = ['/vary/?headers=%s' % urllib.quote_plus(vary) for vary in
            (fragment_header_1, fragment_header_2) if vary]
        html = '\n'.join('<esi:include src="%s" />' % url for url in
            fragment_urls)
        response = HttpResponse(html)
        if main_header:
            response['Vary'] = main_header

        request_url = '/page-with-esi-tags/'
        request.has_attr(_esi={'used': True})
        request.provides('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)

        result = full_process_response(request, response)
        vary_result = result.get('Vary', '')

        for header in (main_header, fragment_header_1, fragment_header_2):
            if not header:
                continue
            vary_fields = cc_delim_re.split(header)
            for field in vary_fields:
                self.assertEqual(len(re.findall(field, vary_result, re.I)), 1)
        
    def test_merges_vary(self):
        vary_sets = (
            (None, None, 'Cookie'),
            (None, 'cookie', 'Cookie'),
            (None, 'Accept-Encoding', 'Cookie'),
            (None, 'Accept-Encoding', 'Cookie, Accept-Language'),
            (None, 'Accept-Encoding, Accept-Language', 'Cookie'),
            ('Accept-Encoding', 'Cookie', 'Cookie'),
        )

        for headers in vary_sets:
            self.check_merged_vary_header(*headers)

    @with_fake_request
    def test_recursive_error_pages(self, request):

        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        request.has_attr(_esi={'used': True})
        response = recursive_404(request)

        patch_data = patch_settings({
            'MIDDLEWARE_CLASSES': MIDDLEWARES,
            'ESI_PROCESS_ERRORS': False,
        })

        result = full_process_response(request, response)
        self.assertEqual(result.content, '')

        restore_settings(*patch_data)
