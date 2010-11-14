from django import template
from django.core.urlresolvers import reverse
import fudge
import random

from .._utils import TestCase

from ...templatetags.esi import EsiNode
from ...templatetags.esi import esi

class TestOfEsiNode(TestCase):
    def test_renders_actual_code(self):
        node = EsiNode('hello_world')
        result = node.render({})

        expected_url = reverse('hello_world')
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

class TestOfEsiHandler(TestCase):
    def test_extracts_view_out_of_templatetag_call(self):
        random_view_name = 'hello_world_%d' % random.randint(100, 200)
        token = fudge.Fake()
        token.expects('split_contents').returns(('esi', random_view_name))
        fudge.clear_calls()

        result = esi(None, token)
        self.assertEquals(result.view_name, random_view_name)

        fudge.verify()

    def test_is_registered_as_a_templatetag_at_esi(self):
        library = template.get_library('esi')
        self.assert_('esi' in library.tags)
        self.assert_(library.tags['esi'] is esi)

    def test_can_be_rendered_from_a_template(self):
        raw_template = """
        {% load esi %}
        {% esi hello_world %}
        """

        t = template.Template(raw_template)
        result = t.render(template.Context()).strip()
        expected_url = reverse('hello_world')
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

