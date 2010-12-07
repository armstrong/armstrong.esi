from django import template
from django.template import defaulttags
from django.template.defaulttags import URLNode


register = template.Library()
esi_tmpl = '<esi:include src="%s" />'

class EsiTemplateTagError(Exception):
    pass

class EsiNode(URLNode):
    def render(self, context):
        try:
            context['_esi']['used'] = True
        except KeyError:
            raise EsiTemplateTagError('The esi templatetag requires the esi context processor, but it isn\'t present.')

        if '/' in self.view_name:
            # An actual URL has been passed instead of a view name, so use it.
            url = self.view_name
        else:
            url = super(EsiNode, self).render(context)

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
