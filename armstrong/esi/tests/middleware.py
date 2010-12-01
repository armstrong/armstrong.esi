from django.http import HttpRequest
from django.http import HttpResponse
from django.utils.cache import cc_delim_re
from django.utils.http import http_date
import fudge
import random
import re
import urllib

from ._utils import TestCase
from ._utils import with_fake_request, with_fake_esi_request

from .. import middleware
from ..middleware import EsiMiddleware
from ..middleware import RequestMiddleware
from ..middleware import ResponseMiddleware


class TestOfResponseEsiMiddleware(TestCase):
    class_under_test = ResponseMiddleware

    @with_fake_request
    def test_adds_esi_token_to_request_object(self, request):
        self.assertFalse(hasattr(request, '_esi_was_invoked'), msg='sanity check')

        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        middleware = self.class_under_test()
        middleware.process_request(request)

        self.assertTrue(hasattr(request, '_esi_was_invoked'))

    def test_esi_token_is_false_by_default(self):
        request = HttpRequest()

        middleware = self.class_under_test()
        middleware.process_request(request)
        self.assertFalse(request._esi_was_invoked)

    @with_fake_esi_request
    def test_returns_unmodified_response_on_non_esi_response(self, request):
        response = random.randint(1000, 2000)
        middleware = self.class_under_test()
        self.assert_(response is middleware.process_response(request, response))

    @with_fake_request
    def test_replaces_esi_tags_with_actual_response(self, request):
        rand = random.randint(100, 200)
        url = '/hello/%d/' % rand

        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        request.has_attr(_esi_was_invoked=[url, ])

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag
        fudge.clear_calls()

        middleware = self.class_under_test()
        result = middleware.process_response(request, response)

        self.assertFalse(re.search(esi_tag, result.content), msg='sanity check')
        self.assertEquals(result.content, str(rand))

    @with_fake_request
    def test_stores_urls_and_original_content_in_cache(self, request):
        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand

        request.has_attr(_esi_was_invoked=[public_url, ])
        request.expects('get_full_path').returns(public_url)
        request.provides('build_absolute_uri').returns('http://example.com%s' % public_url)

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % public_url
        response.content = esi_tag

        expected_cache_data = {
            'content': response.content,
            'urls': [public_url],
        }
        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('set').with_args(public_url, expected_cache_data)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            obj = self.class_under_test()
            result = obj.process_response(request, response)

            self.assertFalse(re.search(esi_tag, result.content), msg='sanity check')
            self.assertEquals(result.content, str(rand), msg='sanity check')

    def get_cookie_test_objs(self, request):
        number = random.randint(100, 200)
        fragment_url = '/cookies/%d/' % number
        request_url = '/page-with-esi-tag/'
        response = HttpResponse('<esi:include src="%s" />' % fragment_url)
        request.has_attr(_esi_was_invoked=[fragment_url])
        request.expects('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)
        return request, response, number

    @with_fake_esi_request
    def test_merges_cookies(self, request):
        request, response, number = self.get_cookie_test_objs(request)
        middleware = self.class_under_test()
        result = middleware.process_response(request, response)

        self.assertEqual(result.cookies['a'].value, 'apple')
        self.assertEqual(result.cookies['b'].value, 'banana')
        self.assertEqual(result.cookies['number'].value, str(number))
        self.assertEqual(result.cookies['b']['path'], '/cookies/')

    @with_fake_esi_request
    def test_main_response_cookies_take_precedence(self, request):
        request, response, number = self.get_cookie_test_objs(request)
        response.set_cookie('a', 'alligator')
        middleware = self.class_under_test()
        result = middleware.process_response(request, response)

        self.assertEqual(result.cookies['a'].value, 'alligator')

    @with_fake_esi_request
    def check_if_max_time_is_last_modified(self, request, main_response_time,
      fragment_time_1, fragment_time_2, max_time):
        fragment_urls = ['/last-modified/%s/' % num for num in
            (fragment_time_1, fragment_time_2)]
        html = '\n'.join('<esi:include src="%s" />' % url for url in
            fragment_urls)
        response = HttpResponse(html)
        response['Last-Modified'] = http_date(main_response_time)

        request_url = '/page-with-esi-tags/'
        request.has_attr(_esi_was_invoked=fragment_urls)
        request.expects('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)

        middleware = self.class_under_test()
        result = middleware.process_response(request, response)

        self.assertTrue(response['Last-Modified'], max_time)

    def test_merges_last_modified(self):
        time_a = random.randint(10000, 20000)
        time_b = random.randint(40000, 50000)
        time_c = random.randint(60000, 70000)

        max_time = http_date(time_c)
        self.check_if_max_time_is_last_modified(time_a, time_b, time_c, max_time)
        self.check_if_max_time_is_last_modified(time_b, time_c, time_a, max_time)
        self.check_if_max_time_is_last_modified(time_c, time_a, time_b, max_time)

    @with_fake_esi_request
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
        request.has_attr(_esi_was_invoked=fragment_urls)
        request.expects('get_full_path').returns(request_url)
        request.provides('build_absolute_uri').returns(
            'http://example.com%s' % request_url)

        middleware = self.class_under_test()
        result = middleware.process_response(request, response)
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


class TestOfRequestMiddleware(TestCase):
    class_under_test = RequestMiddleware

    @with_fake_request
    def test_returns_assembled_HttpResponse_on_cache_hit(self, request):
        foo = random.randint(1000, 2000)

        rand = random.randint(100, 200)
        public_url = '/some-cached-page/%d/' % rand
        url = '/hello/%d/' % rand

        request.has_attr(_esi_was_invoked=['url', ])

        cached_data = {
            'content': '<esi:include src="%s" />' % url,
            'urls': [url],
        }

        request.expects('get_full_path').returns(public_url)
        request.provides('build_absolute_uri').returns('http://example.com%s' % public_url)

        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('get').with_args(public_url).returns(cached_data)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            mw = self.class_under_test()
            result = mw.process_request(request)

            self.assert_(isinstance(result, HttpResponse))
            self.assertEquals(result.content, str(rand))

    @with_fake_request
    def test_returns_None_on_cache_miss(self, request):
        request.provides('get_full_path').returns('/')
        request.provides('build_absolute_uri').returns('http://example.com/')
        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('get').returns(None)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            mw = self.class_under_test()
            self.assertEquals(None, mw.process_request(request))

class TestOfEsiMiddleware(TestOfRequestMiddleware, TestOfResponseEsiMiddleware):
    class_under_test = EsiMiddleware

    def test_extends_RequestMiddleware(self):
        mw = EsiMiddleware()
        self.assert_(isinstance(mw, RequestMiddleware))

    def test_extends_ResponseMiddleware(self):
        mw = EsiMiddleware()
        self.assert_(isinstance(mw, ResponseMiddleware))


