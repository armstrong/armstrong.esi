from django.conf.urls.defaults import patterns, url, handler404

urlpatterns = patterns('armstrong.esi.tests.esi_support.views',
    url(r'^hello/$', 'hello', name='hello_world'),
)
