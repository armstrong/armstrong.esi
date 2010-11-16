from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase as DjangoTestCase
import fudge

def with_fake_request(func):
    def inner(self, *args, **kwargs):
        request = fudge.Fake(HttpRequest)
        request.provides('get_full_path')
        result = func(self, request, *args, **kwargs)

        fudge.verify()
        fudge.clear_expectations()
        return result
    return inner

def with_fake_non_esi_request(func):
    @with_fake_request
    def inner(self, request, *args, **kwargs):
        request.has_attr(_esi_was_invoked=False)
        fudge.clear_calls()
        return func(self, request, *args, **kwargs)
    return inner

def with_fake_esi_request(func):
    @with_fake_request
    def inner(self, request, *args, **kwargs):
        request.has_attr(_esi_was_invoked=True)
        fudge.clear_calls()
        return func(self, request, *args, **kwargs)
    return inner

class TestCase(DjangoTestCase):
    def setUp(self):
        self._original_settings = settings
        fudge.clear_expectations()
        fudge.clear_calls()

    def tearDown(self):
        settings = self._original_settings

