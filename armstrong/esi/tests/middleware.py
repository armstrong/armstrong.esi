import fudge
from ._utils import TestCase
from ._utils import with_fake_request

from ..middleware import BaseEsiMiddleware

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

