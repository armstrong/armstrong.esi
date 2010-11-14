from django.conf import settings
from django.test import TestCase as DjangoTestCase
import fudge

class TestCase(DjangoTestCase):
    def setUp(self):
        self._original_settings = settings

    def tearDown(self):
        settings = self._original_settings

