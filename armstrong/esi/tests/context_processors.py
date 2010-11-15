from django.http import HttpRequest
import random

import fudge
from ._utils import TestCase
from ._utils import with_fake_request

from ..context_processors import esi

class TestOfEsiContextProcessor(TestCase):
    @with_fake_request
    def test_adds_esi_token_to_context(self, request):
        expected_value = random.randint(1000, 2000)
        request._esi_was_invoked = expected_value

        result = esi(request)
        self.assert_('_esi_was_invoked' in result, msg='sanity check')
        self.assertEquals(result['_esi_was_invoked'], expected_value)
