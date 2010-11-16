from django.conf.urls.defaults import *

urlpatterns = patterns('hello.views',
    url(r'^$', 'index'),
    url(r'^esi/$', 'esi', name="some_view"),
)

