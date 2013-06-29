from django import template
from django.template import defaulttags
from django.template.defaulttags import URLNode
from django.utils.text import unescape_string_literal


register = template.Library()
esi_tmpl = '<esi:include src="%s" />'

class EsiTemplateTagError(Exception):
    pass

class EsiNode(URLNode):
    def __init__(self, view_name, *args, **kwargs):
        # Compatibility with Django 1.5 and later
        if hasattr(view_name, 'token'):
            try:
                unescape_string_literal(view_name.token)
            except ValueError:
                # If we cannot unescape the token then it is not quoted.
                # We have to cancel the variables's lookups and tell it
                # that it has a literal value.
                view_name.var.lookups = None
                view_name.var.literal = view_name.token

        super(EsiNode, self).__init__(view_name, *args, **kwargs)

        if '/' in str(self.view_name):
            # An actual URL has been passed instead of a view name.
            self.raw_url = unescape_string_literal(str(self.view_name))
            self.view_name = None
        else:
            self.raw_url = None

    def render(self, context):
        try:
            context['_esi']['used'] = True
        except KeyError:
            raise EsiTemplateTagError('The esi templatetag requires the esi context processor, but it isn\'t present.')

        url = self.raw_url or super(EsiNode, self).render(context)

        if self.asvar:
            url = context[self.asvar]
            context[self.asvar] = esi_tmpl % url
            return ''
        else:
            return esi_tmpl % url

@register.tag
def esi(parser, token):
    url_node = defaulttags.url(parser, token)
    return EsiNode(url_node.view_name, url_node.args, url_node.kwargs,
        url_node.asvar)
