from django.conf.urls.defaults import patterns, url, handler404

urlpatterns = patterns('armstrong.esi.tests.esi_support.views',
    url(r'^hello/$', 'hello', name='hello_world'),
    url(r'^hello/(?P<number>\d+)/$', 'hello', name='hello_number'),
    url(r'^cookies/(?P<number>\d+)/$', 'cookie_view', name='cookie_view'),
    url(r'^last-modified/(?P<timestamp>\d+)/$', 'last_modified', name='last_modified'),
    url(r'^vary/$', 'vary', name='vary'),
    url(r'^500chars/$', 'text', name='text'),
)
