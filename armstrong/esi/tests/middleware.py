from django.http import HttpRequest
from django.http import HttpResponse
import fudge
import random

from ._utils import TestCase
from ._utils import with_fake_request, with_fake_esi_request, with_fake_non_esi_request

from .. import middleware
from ..middleware import BaseEsiMiddleware
from ..middleware import ResponseMiddleware

class TestOfBaseEsiMiddleware(TestCase):
    @with_fake_request
    def test_adds_esi_token_to_request_object(self, request):

        self.assertFalse(hasattr(request, '_esi_was_invoked'), msg='sanity check')

        middleware = BaseEsiMiddleware()
        middleware.process_request(request)

        self.assertTrue(hasattr(request, '_esi_was_invoked'))

    @with_fake_request
    def test_esi_token_is_false_by_default(self, request):
        middleware = BaseEsiMiddleware()
        middleware.process_request(request)
        self.assertFalse(request._esi_was_invoked)

class TestOfResponseEsiMiddleware(TestCase):
    @with_fake_non_esi_request
    def test_returns_unmodified_response_on_non_esi_response(self, request):
        response = random.randint(1000, 2000)
        middleware = ResponseMiddleware()
        self.assert_(response is middleware.process_response(request, response))

    @with_fake_esi_request
    def test_uses_whatever_resolver_was_provided(self, request):
        request._esi_was_invoked = True
        view = fudge.Fake(expect_call=True)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args('/hello/').returns((view, (), {}))
        response = fudge.Fake(HttpResponse)
        response.content = '<esi:include src="/hello/" />'

        fudge.clear_calls()

        middleware = ResponseMiddleware(resolver=resolver)
        middleware.process_response(request, response)

    @with_fake_non_esi_request
    def test_skips_talking_to_the_resolver_on_non_esi_response(self, request):
        resolver = fudge.Fake()
        response = fudge.Fake()
        response.has_attr(content='<esi:include src="/hello/" />')
        fudge.clear_calls()

        self.assertFalse(request._esi_was_invoked, msg='sanity check')
        middleware = ResponseMiddleware(resolver=resolver)
        middleware.process_response(request, response)

    @with_fake_esi_request
    def test_replaces_esi_tags_with_actual_response(self, request):
        rand = random.randint(100, 200)
        url = '/hello-with-random-%d/' % rand

        view = fudge.Fake(expect_call=True)
        view.with_args(request).returns(rand)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag
        fudge.clear_calls()

        middleware = ResponseMiddleware(resolver=resolver)
        result = middleware.process_response(request, response)

        self.assertNotRegexpMatches(result.content, esi_tag, msg='sanity check')
        self.assertEquals(result.content, str(rand))

    def test_stores_urls_and_original_content_in_cache(self):
        request = fudge.Fake(HttpRequest)
        request.has_attr(_esi_was_invoked=True)
        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand
        url = '/hello-with-random-%d/' % rand

        request.expects('get_full_path').returns(public_url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request).returns(rand)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        expected_cache_data = {
            'contents': response.content,
            'urls': [(view, (), {}), ],
        }
        fake_cache = fudge.Fake(middleware.cache)
        fake_cache.expects('set').with_args(public_url, expected_cache_data)

        with fudge.patched_context(middleware, 'cache', fake_cache):
            obj = ResponseMiddleware(resolver=resolver)
            result = obj.process_response(request, response)

            self.assertNotRegexpMatches(result.content, esi_tag, msg='sanity check')
            self.assertEquals(result.content, str(rand), msg='sanity check')

    def test_passes_any_args_along_as_args_to_view(self):
        foo = random.randint(1000, 2000)

        request = fudge.Fake(HttpRequest)
        request.has_attr(_esi_was_invoked=True)
        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand
        url = '/hello-with-random-%d/' % rand

        request.expects('get_full_path').returns(public_url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request, foo).returns(rand)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (foo, ), {}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        obj = ResponseMiddleware(resolver=resolver)
        result = obj.process_response(request, response)

    def test_passes_any_kwargs_along_as_kwargs_to_view(self):
        foo = random.randint(1000, 2000)

        request = fudge.Fake(HttpRequest)
        request.has_attr(_esi_was_invoked=True)
        rand = random.randint(100, 200)
        public_url = '/hello/%d/' % rand
        url = '/hello-with-random-%d/' % rand

        request.expects('get_full_path').returns(public_url)

        view = fudge.Fake(expect_call=True)
        view.with_args(request, value=foo).returns(rand)
        resolver = fudge.Fake()
        resolver.expects('resolve').with_args(url).returns((view, (), {"value": foo}))

        response = fudge.Fake(HttpResponse)
        esi_tag = '<esi:include src="%s" />' % url
        response.content = esi_tag

        obj = ResponseMiddleware(resolver=resolver)
        result = obj.process_response(request, response)

