from django import template
from django.core.urlresolvers import reverse

register = template.Library()

class EsiNode(template.Node):
    def __init__(self, view_name):
        self.view_name = view_name

    def render(self, context):
        context['_esi_was_invoked']['url'] = reverse(self.view_name)
        return '<esi:include src="%s" />' % reverse(self.view_name)

@register.tag
def esi(parser, token):
    tag_name, view_name = token.split_contents()
    return EsiNode(view_name)

