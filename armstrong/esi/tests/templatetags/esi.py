from django import template
from django.core.urlresolvers import reverse
from django.template import Token, Parser, TOKEN_BLOCK
from django.template import FilterExpression
import fudge
import random

from .._utils import TestCase

from ... import context_processors
from ...templatetags.esi import EsiNode
from ...templatetags.esi import esi

def create_context():
    request = fudge.Fake()
    context = template.Context()
    context.update(context_processors.esi(request))
    return context

def create_token(content):
    return Token(TOKEN_BLOCK, content)

class TestOfEsiNode(TestCase):
    def test_renders_actual_code(self):
        context = create_context()
        node = esi(Parser([]), create_token('esi "hello_world"'))
        result = node.render(context)

        expected_url = reverse('hello_world')
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

    def test_renders_relative_esi(self):
        context = create_context()
        node = esi(Parser([]), create_token('esi "./blah/"'))
        result = node.render(context)

        expected_url = './blah/'
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

    def test_renders_kwargs(self):
        context = create_context()
        number = random.randint(100, 200)
        node = esi(Parser([]), create_token('esi "hello_number" number=%s' % number))
        result = node.render(context)

        expected_url = reverse('hello_number', kwargs={'number': number})
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

    def test_sets_esi_used_to_true_on_context(self):
        context = create_context()
        view_name = FilterExpression('"hello_world"', Parser([]))
        node = EsiNode(view_name, [], {}, None)
        node.render(context)

        self.assertTrue(context['_esi']['used'])

class TestOfEsiHandler(TestCase):
    def test_extracts_view_out_of_templatetag_call(self):
        random_view_name = 'hello_world_%d' % random.randint(100, 200)
        token = fudge.Fake()
        token.expects('split_contents').returns(('esi', random_view_name))
        fudge.clear_calls()

        result = esi(Parser([]), token)
        self.assertEquals(str(result.view_name), random_view_name)

        fudge.verify()

    def test_is_registered_as_a_templatetag_at_esi(self):
        library = template.get_library('esi')
        self.assert_('esi' in library.tags)
        self.assert_(library.tags['esi'] is esi)

    def test_can_be_rendered_from_a_template(self):
        raw_template = """
        {% load esi %}
        {% load url from future %}
        {% esi "hello_world" %}
        """

        t = template.Template(raw_template)
        context = create_context()
        result = t.render(context).strip()
        expected_url = reverse('hello_world')
        self.assertEquals(result, '<esi:include src="%s" />' % expected_url)

