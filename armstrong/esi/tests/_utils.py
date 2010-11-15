from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase as DjangoTestCase
import fudge

def with_fake_request(func):
    def inner(self, *args, **kwargs):
        request = fudge.Fake(HttpRequest)
        fudge.clear_calls()

        result = func(self, request, *args, **kwargs)

        fudge.verify()
        fudge.clear_expectations()
        return result
    return inner

class TestCase(DjangoTestCase):
    def setUp(self):
        self._original_settings = settings
        fudge.clear_expectations()
        fudge.clear_calls()

    def tearDown(self):
        settings = self._original_settings

