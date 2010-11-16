from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url('', include('hello.urls')),
)
