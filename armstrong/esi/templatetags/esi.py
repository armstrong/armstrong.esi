from django import template
from django.core.urlresolvers import reverse

register = template.Library()

class EsiTemplateTagError(Exception):
    pass

class EsiNode(template.Node):
    def __init__(self, view_name):
        self.view_name = view_name

    def render(self, context):
        url = reverse(self.view_name)
        try:
            context['_esi']['used'] = True
        except KeyError:
            raise EsiTemplateTagError('The esi templatetag requires the esi context processor, but it isn\'t present.')
        return '<esi:include src="%s" />' % url

@register.tag
def esi(parser, token):
    tag_name, view_name = token.split_contents()
    return EsiNode(view_name)

