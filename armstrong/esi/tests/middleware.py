from django.http import HttpRequest
from django.http import HttpResponse
import fudge
import random

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

    @with_fake_esi_request
    def test_uses_whatever_resolver_was_provided(self, request):
        request._esi_was_invoked = ['/hello/', ]
        request.provides('get_full_path')
        view = fudge.Fake(expect_call=True)
        view.has_attr(content='')
        view.returns(view)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args('/hello/').returns((view, (), {}))
        response = fudge.Fake(HttpResponse)
        response.content = '<esi:include src="/hello/" />'

        fudge.clear_calls()

        middleware = self.class_under_test()
        middleware.process_response(request, response)

    @with_fake_esi_request
    def test_skips_talking_to_the_resolver_on_non_esi_response(self, request):
        resolver = fudge.Fake()
        response = fudge.Fake()
        response.has_attr(content='<esi:include src="/hello/" />')
        fudge.clear_calls()

        self.assertFalse(request._esi_was_invoked, msg='sanity check')
        middleware = self.class_under_test()
        middleware.process_response(request, response)

    @with_fake_request
    def test_replaces_esi_tags_with_actual_response(self, request):
        rand = random.randint(100, 200)
        url = '/hello-with-random-%d/' % rand

        request.has_attr(_esi_was_invoked=[url, ])

        view = fudge.Fake(expect_call=True)
        view.with_args(request).returns(view)
        view.has_attr(content=str(rand))
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag
        fudge.clear_calls()

        middleware = self.class_under_test()
        result = middleware.process_response(request, response)

        self.assertNotRegexpMatches(result.content, esi_tag, msg='sanity check')
        self.assertEquals(result.content, str(rand))

    @with_fake_request
    def test_stores_urls_and_original_content_in_cache(self, request):
        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand

        request.has_attr(_esi_was_invoked=[public_url, ])
        request.expects('get_full_path').returns(public_url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request).returns(view)
        view.has_attr(content=str(rand))
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(public_url).returns((view, (), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % public_url
        response.content = esi_tag

        expected_cache_data = {
            'content': response.content,
            'urls': {public_url: (view, (), {})},
        }
        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('set').with_args(public_url, expected_cache_data)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            obj = self.class_under_test()
            result = obj.process_response(request, response)

            self.assertNotRegexpMatches(result.content, esi_tag, msg='sanity check')
            self.assertEquals(result.content, str(rand), msg='sanity check')

    @with_fake_request
    def test_passes_any_args_along_as_args_to_view(self, request):
        foo = random.randint(1000, 2000)
        rand = random.randint(100, 200)
        url = '/hello/%d/' % rand

        request.has_attr(_esi_was_invoked=[url, ])
        request.expects('get_full_path').returns(url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request, foo).returns(view)
        view.has_attr(content=str(rand))
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (foo, ), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        obj = self.class_under_test()
        result = obj.process_response(request, response)

    @with_fake_request
    def test_passes_any_kwargs_along_as_kwargs_to_view(self, request):
        foo = random.randint(1000, 2000)
        rand = random.randint(100, 200)
        url = '/hello/%d/' % rand

        request.has_attr(_esi_was_invoked=[url, ])
        request.expects('get_full_path').returns(url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request, value=foo).returns(view)
        view.has_attr(content=str(rand))
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {"value": foo}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        obj = self.class_under_test()
        result = obj.process_response(request, response)

class TestOfRequestMiddleware(TestCase):
    class_under_test = RequestMiddleware

    @with_fake_request
    def test_returns_assembled_HttpResponse_on_cache_hit(self, request):
        foo = random.randint(1000, 2000)

        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand
        url = '/hello-with-random-%d/' % rand

        request.has_attr(_esi_was_invoked=['url', ])

        view = fudge.Fake(expect_call=True)
        view.with_args(request).returns(view)
        view.has_attr(content=str(rand))
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {"value": foo}))

        cached_data = {
            'content': '<esi:include src="%s" />' % url,
            'urls': {url: (view, (), {})},
        }

        request.expects('get_full_path').returns(public_url)

        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('get').with_args(public_url).returns(cached_data)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            mw = self.class_under_test()
            result = mw.process_request(request)

            self.assert_(isinstance(result, HttpResponse))
            self.assertEquals(result.content, str(rand))

    @with_fake_request
    def test_returns_None_on_cache_miss(self, request):
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


