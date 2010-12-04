import random

from ._utils import TestCase
from .. import http_client


class ClientTest(TestCase):

    def test_plain_url(self):
        client = http_client.Client()
        self.assertEqual(client.get('/hello/').content, u'Hello World!')

    def test_kwargs_url(self):
        rand = random.randint(100, 200)
        client = http_client.Client()
        self.assertEqual(client.get('/hello/%d/' % rand).content, unicode(rand))

    def test_get_params(self):
        client = http_client.Client()
        expected = 'a = apple, b = banana'
        self.assertEqual(client.get('/hello/?b=banana&a=apple').content, expected)
