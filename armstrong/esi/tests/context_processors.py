from django.http import HttpRequest
import random

import fudge
from ._utils import TestCase
from ._utils import with_fake_request

from ..context_processors import esi

class TestOfEsiContextProcessor(TestCase):
    @with_fake_request
    def test_adds_esi_token_to_context(self, request):
        result = esi(request)
        self.assert_('_esi' in result, msg='sanity check')
        self.assertFalse(result['_esi']['used'])

        request._esi['used'] = True
        result = esi(request)
        self.assert_('_esi' in result, msg='sanity check')
        self.assert_(result['_esi']['used'])
